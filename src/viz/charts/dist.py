"""Pieces shared by the distribution charts (dotplot, histogram, box, strip, ecdf, violin) and the runs= overlays
on bars, hbar and line.

samples()     distribution input ({label: [values]}, grouped lists, pandas) to plain lists
attach_runs() runs= input of bars and hbar, matched to their rows
tukey()       box-plot statistics; quantile() interpolates between ranks like numpy's default
bin_edges()   deterministic histogram bins: Freedman-Diaconis rounded to a 1, 2, 2.5 or 5 width by default
swarm()       a deterministic beeswarm: offsets across the value axis so that dots never overlap
cat_frame()   the value and category axes that box, strip and violin share, vertical or horizontal
free_spot()   direct labels: the first candidate box that crosses no line and no other label
"""
from __future__ import annotations

import bisect
import math
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass

from .. import data as D
from .. import scale as SC
from .. import svg as S
from .. import text as T
from .. import theme as th
from .common import YLABEL_BAND, YLABEL_X

Box = tuple[float, float, float, float]  # x0, y0, x1, y1
Seg = tuple[float, float, float, float]  # x1, y1, x2, y2


# ---------------------------------------------------------------------- input

def is_seq(x) -> bool:
    """A list-like of values: lists, tuples, numpy arrays, pandas Series; not strings or dicts."""
    return not isinstance(x, (str, bytes, Mapping)) and hasattr(x, "__len__") and hasattr(x, "__iter__")


def numbers(vals, what: str = "value") -> list[float]:
    """The numbers in a list, in order. None and NaN mean missing and are dropped; infinities are an error."""
    out = []
    for v in ([] if vals is None else vals):
        f = D._num(v)
        if f is None:
            continue
        if math.isinf(f):
            raise ValueError(f"{what}s must be finite, got {v!r}")
        out.append(f)
    return out


def samples(data, series: Sequence[str] | None = None, flat_label: str | None = None,
            ) -> tuple[list[str], list[list[list[float]]], int, list[str] | None]:
    """Distribution data -> (labels, values[group][series], number of series, series names or None).

    {label: [v, ...]} or [(label, [v, ...]), ...] gives one series per group; {label: [[...], [...]]} gives one list
    per series (name them with series=[...]); a pandas DataFrame gives one group per column. With flat_label set, a
    plain list of numbers is one group of that name. None and NaN values are dropped."""
    if hasattr(data, "columns") and hasattr(data, "index"):  # DataFrame: one group per column
        items = [(str(c), list(data[c])) for c in data.columns]
    elif isinstance(data, Mapping) or (hasattr(data, "items") and hasattr(data, "index")):
        items = list(data.items())
    elif is_seq(data):
        seq = list(data)
        if flat_label is not None and all(not is_seq(v) for v in seq):
            items = [(flat_label, seq)]
        else:
            items = []
            for it in seq:
                if not (is_seq(it) and len(it) == 2):
                    raise TypeError("data should be {label: [values]}, a list of (label, [values]) pairs"
                                    + (", a list of numbers" if flat_label is not None else "") + " or a DataFrame")
                items.append((it[0], it[1]))
    else:
        raise TypeError("data should be {label: [values]}, a list of (label, [values]) pairs or a DataFrame")
    labels, vals, widths = [], [], []
    for label, v in items:
        if v is None:
            groups = None
        elif is_seq(v) and any(is_seq(e) for e in v):
            if not all(e is None or is_seq(e) for e in v):
                raise ValueError(f"group {label!r} mixes numbers and lists: give one list of values, or one per series")
            groups = [numbers(e) for e in v]
        elif is_seq(v):
            groups = [numbers(v)]
        else:
            groups = [numbers([v])]
        labels.append(str(label))
        vals.append(groups)
        if groups is not None:
            widths.append(len(groups))
    ns = max(widths, default=1)
    for label, g in zip(labels, vals):
        if g is not None and len(g) != ns:
            raise ValueError(f"group {label!r} has {len(g)} lists of values, others have {ns}")
    vals = [g if g is not None else [[] for _ in range(ns)] for g in vals]
    if series is not None and len(series) != ns:
        raise ValueError(f"{len(series)} series names for {ns} lists of values per group")
    return labels, vals, ns, None


def attach_runs(rows: list[D.Row], runs, ns: int) -> dict[int, list[list[float]]]:
    """runs= of bars and hbar: {label: [v, ...]} for one series, {label: [[series-1 runs], [series-2 runs]]} for
    grouped bars, or a list aligned with the data rows. Returns {id(row): [runs of each series]}."""
    if runs is None:
        return {}
    data_rows = [r for r in rows if not r.section]
    if isinstance(runs, Mapping) or (hasattr(runs, "items") and hasattr(runs, "index")):
        runs = dict(runs.items())
        known = {r.label for r in data_rows}
        extra = [str(k) for k in runs if str(k) not in known]
        if extra:
            raise ValueError(f"runs for labels that are not in the data: {', '.join(extra)}")
        by_label = {str(k): v for k, v in runs.items()}
        pairs = [(r, by_label.get(r.label)) for r in data_rows]
    else:
        seq = list(runs)
        if len(seq) != len(data_rows):
            raise ValueError(f"runs has {len(seq)} entries for {len(data_rows)} rows")
        pairs = list(zip(data_rows, seq))
    out: dict[int, list[list[float]]] = {}
    for r, x in pairs:
        if x is None:
            continue
        x = list(x) if is_seq(x) else [x]
        nested = any(is_seq(e) for e in x)
        if ns == 1:
            if nested and len(x) != 1:
                raise ValueError(f"runs for {r.label!r}: one list of run values expected, got {len(x)} lists")
            out[id(r)] = [numbers(x[0] if nested else x, "run")]
        else:
            if len(x) != ns or not all(e is None or is_seq(e) for e in x):
                raise ValueError(f"runs for {r.label!r}: expected {ns} lists, one per series")
            out[id(r)] = [numbers(e, "run") for e in x]
    return out


def run_values(runs_of: dict[int, list[list[float]]]) -> list[float]:
    return [v for per_series in runs_of.values() for vs in per_series for v in vs]


# ---------------------------------------------------------------------- statistics

def quantile(s: Sequence[float], q: float) -> float:
    """The q-quantile of sorted numbers, interpolating between ranks (numpy's default method)."""
    if not s:
        raise ValueError("quantile of no values")
    pos = (len(s) - 1) * q
    i = math.floor(pos)
    if i >= len(s) - 1:
        return float(s[-1])
    return s[i] + (s[i + 1] - s[i]) * (pos - i)


@dataclass
class Tukey:
    q1: float
    median: float
    q3: float
    low: float   # whisker ends: the most extreme values within 1.5 IQR of the box
    high: float
    outliers: list[float]


def tukey(vals: Iterable[float]) -> Tukey:
    s = sorted(vals)
    q1, med, q3 = quantile(s, 0.25), quantile(s, 0.5), quantile(s, 0.75)
    k = 1.5 * (q3 - q1)
    eps = 1e-9 * max(1.0, abs(q1), abs(q3))
    lo_f, hi_f = q1 - k - eps, q3 + k + eps
    inside = [v for v in s if lo_f <= v <= hi_f]
    low = min(inside[0], q1) if inside else q1
    high = max(inside[-1], q3) if inside else q3
    return Tukey(q1, med, q3, low, high, [v for v in s if v < lo_f or v > hi_f])


def mean(vals: Sequence[float]) -> float:
    return sum(vals) / len(vals)


_T975 = [12.706, 4.303, 3.182, 2.776, 2.571, 2.447, 2.365, 2.306, 2.262, 2.228, 2.201, 2.179, 2.160, 2.145, 2.131,
         2.120, 2.110, 2.101, 2.093, 2.086, 2.080, 2.074, 2.069, 2.064, 2.060, 2.056, 2.052, 2.048, 2.045, 2.042]


def t975(df: int) -> float:
    """Critical value of Student's t for a two-sided 95% interval (a table to 30, then Cornish-Fisher)."""
    if df < 1:
        raise ValueError("t needs at least one degree of freedom")
    if df <= len(_T975):
        return _T975[df - 1]
    z = 1.959964
    return z + (z ** 3 + z) / (4 * df) + (5 * z ** 5 + 16 * z ** 3 + 3 * z) / (96 * df ** 2)


def mean_ci(vals: Sequence[float]) -> tuple[float, float] | None:
    """95% t interval of the mean; None for fewer than two values."""
    n = len(vals)
    if n < 2:
        return None
    m = mean(vals)
    sd = math.sqrt(sum((v - m) ** 2 for v in vals) / (n - 1))
    h = t975(n - 1) * sd / math.sqrt(n)
    return m - h, m + h


# ---------------------------------------------------------------------- histogram bins

def nice_width(h: float) -> float:
    """The 1, 2, 2.5 or 5 times a power of ten nearest to h (by ratio)."""
    if not h > 0 or math.isinf(h):
        return 1.0
    mag = 10 ** math.floor(math.log10(h))
    return min((m * mag for m in (1, 2, 2.5, 5, 10)), key=lambda c: abs(math.log(c / h)))


def whole(vals: Iterable[float]) -> bool:
    vals = list(vals)
    return bool(vals) and all(float(v).is_integer() for v in vals)


def bin_edges(vals: Sequence[float], bins=None, span: tuple[float, float] | None = None) -> list[float]:
    """Histogram bin edges.

    bins=None: the Freedman-Diaconis width 2 IQR / n^(1/3), rounded to a 1, 2, 2.5 or 5 width, with edges on
    multiples of it; whole-number data gets a whole-number width with edges halfway between values, so each bar
    sits centered on the values it counts. bins=int: that many equal bins from the lowest to the highest value.
    bins=[e0, e1, ...]: those edges. span: the (lo, hi) range to cover instead of the data's."""
    if bins is not None and not isinstance(bins, bool) and is_seq(bins):
        edges = sorted({float(b) for b in bins})
        if len(edges) < 2:
            raise ValueError("bins needs at least two different edges")
        return edges
    s = sorted(vals)
    lo, hi = span if span is not None else ((s[0], s[-1]) if s else (0.0, 1.0))
    if isinstance(bins, int) and not isinstance(bins, bool):
        if bins < 1:
            raise ValueError("bins must be at least 1")
        if hi <= lo:
            lo, hi = lo - 0.5, hi + 0.5
        return [lo + (hi - lo) * k / bins for k in range(bins)] + [hi]
    if bins is not None:
        raise TypeError("bins: None (Freedman-Diaconis), a number of bins, or a list of edges")
    n = len(s)
    integral = whole(s)
    iqr = quantile(s, 0.75) - quantile(s, 0.25) if n else 0.0
    if iqr > 0:
        h = 2 * iqr / n ** (1 / 3)
    elif hi > lo:
        h = (hi - lo) / (math.ceil(math.log2(max(n, 1))) + 1)  # Sturges, when the middle half is a single value
    else:
        h = 1.0
    w = nice_width(max(h, (hi - lo) / 150))  # no more than about 150 bins
    if integral:
        w = float(max(1, round(w)))
    if integral and w == 1:  # one bar per value, centered on it
        start = lo - 0.5
        k = round(hi - lo) + 1
    else:
        start = math.floor(lo / w + 1e-9) * w
        k = max(1, math.ceil((hi - start) / w - 1e-9))
        if integral and start + k * w == hi:  # whole numbers: keep the top value out of the closed last edge
            k += 1
    return [round(start + i * w, 10) for i in range(k + 1)]


def bin_counts(vals: Iterable[float], edges: Sequence[float]) -> list[int]:
    """Values per bin; bins include their left edge, the last also its right edge. Values outside are skipped."""
    c = [0] * (len(edges) - 1)
    for v in vals:
        if v < edges[0] or v > edges[-1]:
            continue
        i = min(bisect.bisect_right(edges, v) - 1, len(c) - 1)
        c[i] += 1
    return c


# ---------------------------------------------------------------------- dots

def dark(c: str) -> str:
    """A darker shade of a mark's color, for dots drawn over it (runs over bars, points over boxes)."""
    return th.mix(c, th.INK, 0.4)


def swarm(pos: Sequence[float], r: float, limit: float | None = None, gap: float = 0.6) -> list[float]:
    """A deterministic beeswarm. pos: each dot's coordinate along the value axis (px). Returns each dot's offset
    across that axis such that dots of radius r never overlap. Dots are placed from the lowest position up, each at
    the free offset nearest the center line, then each cluster is centered. If the swarm is wider than +-limit, all
    offsets shrink to fit, and the dots overlap a little. Above 400 dots it spreads them evenly by rank instead."""
    n = len(pos)
    if n == 0:
        return []
    d = 2 * r + gap
    order = sorted(range(n), key=lambda i: (pos[i], i))
    out = [0.0] * n
    if n > 400:
        half = max(limit, 0.0) if limit is not None else 4 * d
        for rank, i in enumerate(order):
            out[i] = ((rank * 0.6180339887498949) % 1 - 0.5) * 2 * half
        return out
    placed: list[tuple[float, float]] = []  # (position, offset), positions ascending
    for i in order:
        p = pos[i]
        near = []
        for q, o in reversed(placed):
            if p - q >= d:
                break
            near.append((q, o))
        cands = [0.0]
        for q, o in near:
            dx = math.sqrt(max(d * d - (p - q) ** 2, 0.0))
            cands += [o + dx, o - dx]
        cands.sort(key=lambda c: (abs(c), -c))
        best = cands[-1]
        for c in cands:
            if all((c - o) ** 2 + (p - q) ** 2 >= d * d - 1e-6 for q, o in near):
                best = c
                break
        out[i] = best
        placed.append((p, best))
    start = 0  # center each cluster of dots that touch along the axis
    for k in range(1, n + 1):
        if k == n or pos[order[k]] - pos[order[k - 1]] >= d:
            members = order[start:k]
            shift = (max(out[i] for i in members) + min(out[i] for i in members)) / 2
            for i in members:
                out[i] -= shift
            start = k
    if limit is not None:
        lim = max(limit, 0.0)
        widest = max(abs(o) for o in out)
        if widest > lim:
            out = [o * lim / widest for o in out]
    return out


def dots(pos: Sequence[float], center: float, half: float, r: float, fill: str, horizontal: bool,
         stroke_width: float = 1.0) -> str:
    """Circles at value-axis positions pos, swarmed across the axis within center +- half."""
    offs = swarm(pos, r, half - r - 0.5)
    out = []
    for p, o in sorted(zip(pos, offs)):
        x, y = (p, center + o) if horizontal else (center + o, p)
        out.append(S.circle(x, y, r, fill, th.BG, stroke_width))
    return "".join(out)


# ---------------------------------------------------------------------- the category axis of box, strip, violin

@dataclass
class CatFrame:
    svg: list[str]                         # axes, ticks, labels and the reference line
    height: float
    val: Callable[[float], float]          # value -> px along the value axis
    center: Callable[[int, int], float]    # (group, series) -> px along the category axis
    slot: float                            # thickness of one series' slot across the category axis
    horizontal: bool
    meta: dict
    bands: list[tuple[float, float]]       # each group's extent along the category axis
    plot: tuple[float, float]              # the value axis's extent (px)

    def xy(self, v: float, c: float) -> tuple[float, float]:
        """(px along the value axis, px along the category axis) -> (x, y)."""
        return (v, c) if self.horizontal else (c, v)

    def seg(self, v0: float, c0: float, v1: float, c1: float, stroke: str, w: float = 1.0, cap: str | None = None) -> str:
        x0, y0 = self.xy(v0, c0)
        x1, y1 = self.xy(v1, c1)
        return S.line(x0, y0, x1, y1, stroke, w, cap=cap)

    def rect(self, v0: float, v1: float, c0: float, c1: float, fill: str) -> str:
        a, b = min(v0, v1), max(v0, v1)
        if self.horizontal:
            return S.rect(a, c0, b - a, c1 - c0, fill)
        return S.rect(c0, a, c1 - c0, b - a, fill)


def axis_domain(ext: list[float], unit: str, domain, ticks, step, zero: bool, compact: bool = False,
                ) -> tuple[float, float, list[float]]:
    if ticks is not None:
        return min(ticks), max(ticks), list(ticks)
    if domain is not None:
        return SC.domain(ext, domain[0], domain[1], unit == "%", step=step)
    return SC.domain(ext, percent=unit == "%", zero=zero, step=step, full_percent_step=25 if compact else 20)


def cat_frame(W: float, labels: list[str], ns: int, ext: list[float], *, horizontal: bool, unit: str,
              signed: bool = False, domain=None, ticks=None, step=None, zero: bool = True, tick_format=None,
              axis_title: str | None = None, ref: float | None = None, ref_label: str | None = None,
              height: float | None = None, grid: bool = False, bold: Iterable[str] = (),
              slot_v: Callable[[float], float] | None = None, slot_h: float = 22.0, row_height: float | None = None,
              ends: Iterable[tuple[float, float]] = (), cat_lines: int = 0) -> CatFrame:
    """Axes for charts with groups along one axis and values along the other.

    Vertical (the default) copies the bars look: groups along the bottom with wrapped labels, left and bottom axis
    lines, ticks on the left and a rotated axis title. Horizontal copies hbar: labels on the left, light vertical
    gridlines and ticks below. slot_v(group width) is the width of one series' slot when vertical, slot_h its
    thickness when horizontal. ends: (value, px) pairs for labels written right of a value when horizontal, so the
    axis leaves room for them."""
    n = len(labels)
    gap = 3.0
    out: list[str] = []
    if not horizontal:
        compact = W < 520
        lo, hi, tk = axis_domain(ext, unit, domain, ticks, step, zero, compact)
        span = (hi - lo) or 1.0
        tfmt = SC.tick_formatter(tk, unit, signed, tick_format)
        tw = max((T.width(tfmt(t), th.TICK_SIZE) for t in tk), default=0.0)
        m_l = max(48.0 if compact else 58.0, tw + 13 + (YLABEL_BAND if axis_title else 2))  # ticks end 9 px left
        m_r, m_t = 10.0, 22.0
        pw = W - m_l - m_r
        gw = pw / max(n, 1)
        lines = [T.wrap(lab, gw - 8, 12) for lab in labels]
        depth = max(max((len(x) for x in lines), default=1), cat_lines)
        m_b = 16 + depth * 15
        H = height or (270 if compact else 300)
        ph = H - m_t - m_b
        val = lambda v: m_t + ph * (1 - (min(max(v, lo), hi) - lo) / span)
        sw = slot_v(gw) if slot_v else min(46.0, gw * 0.5)
        total = ns * sw + (ns - 1) * gap
        center = lambda i, j: m_l + gw * (i + 0.5) - total / 2 + j * (sw + gap) + sw / 2
        for t in tk:
            if grid and t > lo:
                out.append(S.line(m_l, val(t), W - m_r, val(t), th.GRID))
            out.append(S.text(m_l - 9, val(t) + 4, tfmt(t), th.TICK_SIZE, th.MUTED, "end"))
        out.append(S.line(m_l, m_t - 4, m_l, m_t + ph, th.AXIS))
        out.append(S.line(m_l, m_t + ph, W - m_r, m_t + ph, th.AXIS))
        if lo < 0 < hi:
            out.append(S.line(m_l, val(0), W - m_r, val(0), th.MUTED))
        if ref is not None:
            out.append(S.line(m_l, val(ref), W - m_r, val(ref), th.MUTED, 1, "4 4"))
            if ref_label:
                out.append(S.text(W - m_r, val(ref) - 6, ref_label, 12, th.MUTED, "end", halo=th.BG))
        if axis_title:
            out.append(S.rotated(YLABEL_X, m_t + ph / 2, axis_title, size=12))
        for i, ln in enumerate(lines):
            for k, s in enumerate(ln):
                out.append(S.text(m_l + gw * (i + 0.5), m_t + ph + 19 + k * 15, s, 12, th.INK2, "middle"))
        bands = [(m_l + gw * i, m_l + gw * (i + 1)) for i in range(n)]
        return CatFrame(out, H, val, center, sw, False, {"cat_lines": depth, "plot_x": (m_l, W - m_r)}, bands,
                        (m_t, m_t + ph))

    lo, hi, tk = axis_domain(ext, unit, domain, ticks, step, zero)
    span = (hi - lo) or 1.0
    tfmt = SC.tick_formatter(tk, unit, signed, tick_format)
    bold = set(bold)
    ls = 13.5 if n <= 8 else 12.5

    def style(lab):
        return (ls + 1, 600, th.INK) if lab in bold else (ls, 400, th.INK2)
    max_lab = 0.42 * W
    lab_lines = []
    for lab in labels:
        size, wt, _ = style(lab)
        too_wide = T.width(lab, size, "sans", wt) > max_lab
        lab_lines.append(T.wrap_balanced(lab, max_lab, size, "sans", wt) if too_wide else [lab])
    L = max((max(T.width(s, style(lab)[0], "sans", style(lab)[1]) for s in ln)
             for lab, ln in zip(labels, lab_lines)), default=40.0) + 14
    L = max(L, 0.24 * W)
    R0 = min(W - (T.width(tfmt(hi), th.TICK_SIZE) / 2 + 2), W - 0.06 * W)
    for v, px in ends:
        t = (v - lo) / span
        if t > 0:
            R0 = min(R0, L + (W - 2 - px - L) / t)
    R0 = max(R0, L + 40)
    val = lambda v: L + (R0 - L) * (min(max(v, lo), hi) - lo) / span
    inner = ns * slot_h + (ns - 1) * gap
    top = 18.0 if ref_label else 4.0
    rows: list[tuple[float, float]] = []
    y = top
    for lab, ln in zip(labels, lab_lines):
        h = max(row_height or inner + 22, len(ln) * style(lab)[0] * 1.25 + 8)
        rows.append((y, h))
        y += h
    bottom = y
    center = lambda i, j: rows[i][0] + rows[i][1] / 2 - inner / 2 + j * (slot_h + gap) + slot_h / 2
    for t in tk:
        out.append(S.line(val(t), top, val(t), bottom, th.GRID))
        out.append(S.text(val(t), bottom + 20, tfmt(t), th.TICK_SIZE, th.MUTED, "middle"))
    if ref is not None:
        out.append(S.line(val(ref), top, val(ref), bottom, th.INK2, 1.2))
        if ref_label:
            out.append(S.text(val(ref), top - 6, ref_label, 12, th.MUTED, "middle"))
    for lab, ln, (yy, h) in zip(labels, lab_lines, rows):
        size, wt, fill = style(lab)
        lh = size * 1.25
        first = yy + h / 2 - (len(ln) - 1) * lh / 2 + size * 0.36
        for k, s in enumerate(ln):
            out.append(S.text(L - 14, first + k * lh, s, size, fill, "end", wt))
    H = bottom + 30
    if axis_title:
        out.append(S.text((L + R0) / 2, bottom + 46, axis_title, 12.5, th.INK2, "middle"))
        H += 24
    return CatFrame(out, H, val, center, slot_h, True, {"plot_x": (L, R0)}, [(a, a + h) for a, h in rows],
                    (L, W))


def summary_labels(f: CatFrame, marks: list[tuple[int, int, float, float, str]], ns: int,
                   size: float = 12.5) -> list[str] | None:
    """Labels for the summary value of each mark (a box's median, a strip's mean), written beside the mark where
    the value is: right of it when vertical (left for the first of two series), above it when horizontal (below for
    the second of two). marks: (group, series, value px, the mark's half-width px, text). None when there are more
    than two series or a label would leave its group's band."""
    if ns > 2:
        return None
    out = []
    for i, j, v, reach, s in marks:
        w = T.width(s, size)
        c = f.center(i, j)
        lo, hi = f.bands[i]
        first = ns == 2 and j == 0
        if f.horizontal:
            above = ns == 1 or first
            top = c - reach - 4 - size if above else c + reach + 4
            if top < lo or top + size > hi or v - w / 2 < f.plot[0] or v + w / 2 > f.plot[1]:
                return None
            out.append(S.text(v, top + size * 0.76, s, size, th.INK2, "middle", halo=th.BG))
        else:
            if first:
                x, anchor, x0 = c - reach - 6, "end", c - reach - 6 - w
            else:
                x, anchor, x0 = c + reach + 6, "start", c + reach + 6
            if x0 < lo + 1 or x0 + w > hi - 1:
                return None
            out.append(S.text(x, v + size * 0.36, s, size, th.INK2, anchor, halo=th.BG))
    return out


# ---------------------------------------------------------------------- direct labels

LABEL_SIZE = 12.5


def seg_hits(s: Seg, b: Box) -> bool:
    """Whether a line segment touches a box (Liang-Barsky clipping)."""
    x1, y1, x2, y2 = s
    bx0, by0, bx1, by1 = b
    dx, dy = x2 - x1, y2 - y1
    t0, t1 = 0.0, 1.0
    for p, q in ((-dx, x1 - bx0), (dx, bx1 - x1), (-dy, y1 - by0), (dy, by1 - y1)):
        if p == 0:
            if q < 0:
                return False
            continue
        t = q / p
        if p < 0:
            if t > t1:
                return False
            t0 = max(t0, t)
        else:
            if t < t0:
                return False
            t1 = min(t1, t)
    return t0 <= t1


def boxes_meet(a: Box, b: Box, pad: float = 0.0) -> bool:
    return not (a[2] + pad <= b[0] or b[2] + pad <= a[0] or a[3] + pad <= b[1] or b[3] + pad <= a[1])


def free_spot(cands: Iterable[Box], segs: Sequence[Seg], taken: Sequence[Box], area: Box,
              pad: tuple[float, float] = (5.0, 1.0)) -> Box | None:
    """The first candidate box inside `area` that keeps `pad` (x, y) px clear of every segment and taken box."""
    px, py = pad
    for b in cands:
        if b[0] < area[0] or b[1] < area[1] or b[2] > area[2] or b[3] > area[3]:
            continue
        if any(boxes_meet(b, t, 2) for t in taken):
            continue
        g = (b[0] - px, b[1] - py, b[2] + px, b[3] + py)
        if any(not (max(s[0], s[2]) < g[0] or min(s[0], s[2]) > g[2] or max(s[1], s[3]) < g[1]
                    or min(s[1], s[3]) > g[3]) and seg_hits(s, g) for s in segs):
            continue
        return b
    return None


def key_width(name: str) -> float:
    """Width of a direct label: a small key in the series color, then the name."""
    return 18 + T.width(name, LABEL_SIZE, "sans", 600)


def key_label(b: Box, name: str, color: str, shape: str = "line") -> str:
    """A direct label in box b: a short line (or square) key in the series color, then the name in ink."""
    cy = (b[1] + b[3]) / 2
    key = (S.line(b[0] + 1, cy, b[0] + 12, cy, color, 2.5, cap="round") if shape == "line"
           else S.rect(b[0] + 1, cy - 5, 10, 10, color, 2))
    return key + S.text(b[0] + 18, cy + LABEL_SIZE * 0.36, name, LABEL_SIZE, th.INK2, weight=600, halo=th.BG)
