"""What the line and area charts share: the x axis (linear, category or log), log ticks for a y axis, labeled marks
at x values, and end labels pushed apart so they don't overlap.

Powers of ten outside 0.001 to 1,000 are written 10 with a raised exponent; every other tick is a plain number.
"""
from __future__ import annotations

import bisect
import math
from collections.abc import Callable, Mapping, Sequence

from .. import scale as SC
from .. import svg as S
from .. import text as T
from .. import theme as th

XSCALES = ("linear", "category", "log")
MANY = 12          # past this many x values, a linear x axis ticks at round steps instead of at every value
MARK_GAP = 10      # px between two mark labels
MARK_ROW = 16      # px per row of mark labels above the plot
EXP, RISE = 0.72, 0.42  # a raised exponent's size and lift, as shares of the tick size


def check_xscale(xscale) -> None:
    if xscale not in XSCALES:
        raise ValueError(f"xscale={xscale!r}: use 'linear', 'category' or 'log'")


def by_number(m: Mapping) -> dict:
    """{x: value} with keys read as numbers where they can be, so a JSON spec's "500" finds the x value 500."""
    out = {}
    for k, v in m.items():
        try:
            out[float(k)] = v
        except (TypeError, ValueError):
            out[k] = v
    return out


# ---------------------------------------------------------------------------------------------------- x axis

def x_ticks(xs: Sequence[float], xticks=None, xscale: str = "linear", xtick_labels=None,
            extra: Sequence[float] = ()) -> list[float]:
    """Where the x ticks go: the given ticks; one per power of ten on a log axis; on a linear axis with more than
    MANY x values, round steps (or the keys of an xtick_labels mapping); else every x value. extra: x values the
    axis must also reach, such as marks."""
    if xticks is not None:
        return list(xticks)
    span = list(xs) + list(extra)
    if xscale == "log" and span and min(span) > 0:  # one tick per power of ten
        e0 = math.floor(math.log10(min(span)) + 1e-9)
        e1 = math.ceil(math.log10(max(span)) - 1e-9)
        return [10.0 ** k for k in range(e0, e1 + 1)]
    if xscale == "linear" and len(xs) > MANY and (xtick_labels is None or isinstance(xtick_labels, Mapping)):
        if isinstance(xtick_labels, Mapping):
            return sorted(k for k in by_number(xtick_labels) if isinstance(k, float))
        return round_ticks(min(span), max(span), all(float(v).is_integer() for v in span))
    return list(xs)


def round_ticks(lo: float, hi: float, whole: bool = False) -> list[float]:
    """About five round steps inside [lo, hi]; whole numbers only when the values are whole (epochs, steps)."""
    st = SC.nice_step(hi - lo, 5)
    if whole:
        st = max(1.0, float(math.floor(st)))  # 2.5 -> 2
    return SC.ticks(math.ceil(lo / st - 1e-9) * st, hi, st)


def x_labeler(xtick_labels, xt: Sequence[float], xunit: str = "", xscale: str = "linear") -> Callable[[float], str]:
    """The text of each x tick: xtick_labels ({x: "label"} or a list matching the ticks), plain numbers each with
    their own decimals on a log axis, else numbers sharing the ticks' decimals."""
    if isinstance(xtick_labels, Mapping):
        m = by_number(xtick_labels)
        return lambda v: m.get(v, SC.fmt_num(v, 0, xunit))
    if xtick_labels is not None:
        m = dict(zip(xt, xtick_labels))
        return lambda v: m.get(v, "")
    if xscale == "log":
        return lambda v: log_text(v, xunit)
    return SC.tick_formatter(list(xt), xunit)


def x_scale(xscale: str, xt: Sequence[float], xs: Sequence[float], left: float, width: float,
            extra: Sequence[float] = ()) -> Callable[[float], float]:
    """Pixel x of an x value. category: the values evenly spaced in order; log and linear: from the smallest to the
    largest of the ticks, the x values and `extra` (marks)."""
    if xscale == "category":
        order = sorted(set(xt) | set(xs))
        return lambda v: left + width * (order.index(v) / (len(order) - 1) if len(order) > 1 else 0.5)
    vals = list(xt) + list(xs) + list(extra)
    x0, x1 = min(vals), max(vals)
    if xscale == "log":
        if x0 <= 0:
            raise ValueError("xscale='log' needs x values above 0")
        return lambda v: left + width * (math.log(v / x0) / math.log(x1 / x0) if x1 > x0 else 0.5)
    return lambda v: left + width * ((v - x0) / (x1 - x0) if x1 > x0 else 0.5)


# ---------------------------------------------------------------------------------------------------- tick labels

def _power(t: float) -> int | None:
    """k when t is 10^k outside 0.001..1,000 (written with a raised exponent), else None."""
    if t <= 0:
        return None
    k = round(math.log10(t))
    return k if abs(10.0 ** k - t) < 1e-9 * t and not -3 <= k <= 3 else None


def log_text(t: float, unit: str = "") -> str:
    """A tick on a log axis as a plain number with only the decimals it needs: 0.001, 0.5, 20, 1,000."""
    s = f"{t:.6f}".rstrip("0").rstrip(".")
    return SC.fmt_num(t, len(s.split(".")[1]) if "." in s else 0, unit)


def tick_text(x: float, y: float, t: float, anchor: str, label: Callable[[float], str], power: bool = False,
              unit: str = "") -> str:
    """One tick label. power=True writes a power of ten outside 0.001..1,000 as 10 with a raised exponent."""
    k = _power(t) if power else None
    if k is None:
        return S.text(x, y, label(t), th.TICK_SIZE, th.MUTED, anchor)
    parts = [("10", {"size": th.TICK_SIZE, "fill": th.MUTED}),
             (str(k).replace("-", SC.MINUS), {"size": th.TICK_SIZE * EXP, "fill": th.MUTED, "dy": -th.TICK_SIZE * RISE})]
    if unit:
        parts.append((unit, {"size": th.TICK_SIZE, "fill": th.MUTED, "dy": th.TICK_SIZE * RISE}))
    return S.spans(x, y, parts, anchor)


def tick_width(t: float, label: Callable[[float], str], power: bool = False, unit: str = "") -> float:
    k = _power(t) if power else None
    if k is None:
        return T.width(label(t), th.TICK_SIZE)
    return (T.width("10", th.TICK_SIZE) + T.width(str(k).replace("-", SC.MINUS), th.TICK_SIZE * EXP)
            + T.width(unit, th.TICK_SIZE))


# ---------------------------------------------------------------------------------------------------- log y axis

def log_ticks(vmin: float, vmax: float, lo: float | None = None, hi: float | None = None
              ) -> tuple[float, float, list[float]]:
    """(lo, hi, ticks) for a log axis over vmin..vmax: a tick at each power of ten, the ends snapped out to powers of
    ten. When the values fill too little of three or more powers of ten, and sit between 0.001 and 1,000 (so every
    tick is a plain number), the ticks step 1, 2, 3, ... 9 times a power of ten (up to six ticks) or 1, 2, 5 times
    one instead, such as 2, 3, 4, 5 for a loss. lo and hi, when given, fix the ends."""
    a = lo if lo is not None else vmin
    b = hi if hi is not None else vmax
    e0 = math.floor(math.log10(a) + 1e-9)
    e1 = max(math.ceil(math.log10(b) - 1e-9), e0 + 1)
    plain = e0 >= -3 and e1 <= 3
    first = None
    for mults in ((1,), (1, 2, 3, 4, 5, 6, 7, 8, 9), (1, 2, 5)):
        if mults != (1,) and not plain:
            break
        cands = sorted({float(f"{m}e{k}") for k in range(e0, e1 + 1) for m in mults})
        lo_ = lo if lo is not None else max([c for c in cands if c <= a * (1 + 1e-9)], default=cands[0])
        hi_ = hi if hi is not None else min([c for c in cands if c >= b * (1 - 1e-9)], default=cands[-1])
        if hi_ <= lo_:
            hi_ = min([c for c in cands if c > lo_ * (1 + 1e-9)], default=lo_ * 10)
        tk = [c for c in cands if lo_ * (1 - 1e-9) <= c <= hi_ * (1 + 1e-9)]
        if mults == (1,):
            first = (lo_, hi_, tk)
            fill = math.log(b / a) / math.log(hi_ / lo_) if b > a else 0.0
            if len(tk) >= 3 and fill >= 0.5:
                return first
        elif 2 <= len(tk) <= (6 if len(mults) == 9 else 8):
            return lo_, hi_, tk
    lo_, hi_, tk = first
    return lo_, hi_, tk or [lo_, hi_]


def log_axis(values: Sequence[float], ticks=None, domain=None) -> tuple[float, float, list[float]]:
    """(lo, hi, ticks) of a log y axis over the values; ticks= and domain= (either end may be None) as on a linear
    axis. Every value must be above 0."""
    if ticks is not None:
        tk = sorted(float(t) for t in ticks)
        if not tk or tk[0] <= 0:
            raise ValueError("yscale='log' needs ticks above 0")
        return tk[0], tk[-1], tk
    vals = [v for v in values if v is not None]
    vmin, vmax = (min(vals), max(vals)) if vals else (1.0, 10.0)
    lo, hi = (None, None) if domain is None else domain
    if (lo is not None and lo <= 0) or (hi is not None and hi <= 0) or (lo is not None and hi is not None and hi <= lo):
        raise ValueError(f"yscale='log' needs a domain with 0 < lo < hi, got {domain!r}")
    return log_ticks(vmin, vmax, lo, hi)


# ---------------------------------------------------------------------------------------------------- marks

def read_marks(marks) -> list[tuple[float, str]]:
    """{x: "label"} as [(x, label)] in x order. A JSON spec's "500" reads as 500; None or "" draws the line alone."""
    if marks is None:
        return []
    if not isinstance(marks, Mapping):
        raise TypeError('marks: give {x: "label"}, such as {500: "RL starts"}')
    out = []
    for k, v in marks.items():
        try:
            x = float(k)
        except (TypeError, ValueError):
            raise ValueError(f"marks: {k!r} is not an x value") from None
        if not math.isfinite(x):
            raise ValueError(f"marks: {k!r} is not an x value")
        out.append((x, "" if v is None else str(v)))
    return sorted(out)


def check_marks(marks: list[tuple[float, str]], xscale: str, xs: Sequence[float]) -> None:
    """Marks on a log axis need x above 0; on a category axis, x must be one of the x values."""
    for x, _ in marks:
        if xscale == "log" and x <= 0:
            raise ValueError(f"marks at x={x:g}: xscale='log' needs x values above 0")
        if xscale == "category" and x not in set(xs):
            raise ValueError(f"marks at x={x:g}, which is not one of the x values; xscale='category' places marks "
                             "only at x values")


def mark_layout(marks: list[tuple[float, str]], X: Callable[[float], float], lo: float, hi: float
                ) -> tuple[list[tuple[float, str, int]], int]:
    """Where each mark's label goes above the plot: centered over its line, pushed apart MARK_GAP px and kept inside
    lo..hi, all in one row while every label still sits over its own line; else in rows, each label centered over
    its line in the first row it fits. Returns ([(label left x, label, row)], number of rows)."""
    items = sorted(((X(x), lab, T.width(lab, th.MIN_TEXT)) for x, lab in marks if lab), key=lambda it: it[0])
    if not items:
        return [], 0
    left = [min(max(c - w / 2, lo), hi - w) for c, _, w in items]
    for k in range(1, len(items)):  # push right past the label before, then back left from the right edge
        left[k] = max(left[k], left[k - 1] + items[k - 1][2] + MARK_GAP)
    for k in range(len(items) - 1, -1, -1):
        end = hi if k == len(items) - 1 else left[k + 1] - MARK_GAP
        left[k] = min(left[k], end - items[k][2])
    if left[0] >= lo - 1e-6 and all(x0 - 1e-6 <= c <= x0 + w + 1e-6 for (c, _, w), x0 in zip(items, left)):
        return [(x0, lab, 0) for (_, lab, _), x0 in zip(items, left)], 1
    rows: list[list[tuple[float, float]]] = []
    out = []
    for c, lab, w in items:
        x0 = max(lo, min(c - w / 2, hi - w))
        r = next((r for r, row in enumerate(rows) if all(x0 >= b + MARK_GAP or x0 + w + MARK_GAP <= a for a, b in row)),
                 len(rows))
        if r == len(rows):
            rows.append([])
        rows[r].append((x0, x0 + w))
        out.append((x0, lab, r))
    return out, len(rows)


def mark_lines(marks: list[tuple[float, str]], X: Callable[[float], float], top: float, bottom: float,
               color: str) -> str:
    """A thin dashed vertical line at each mark."""
    return "".join(S.line(X(x), top, X(x), bottom, color, 1, "4 4") for x, _ in marks)


def mark_labels(layout: list[tuple[float, str, int]], top: float) -> str:
    """The mark labels in their rows above the plot top."""
    return "".join(S.text(x0, top - 9 - MARK_ROW * r, lab, th.MIN_TEXT, th.MUTED) for x0, lab, r in layout)


# ---------------------------------------------------------------------------------------------------- end labels

def spread(ys: Sequence[float], gap: float, bottom: float) -> list[float]:
    """Positions in increasing order pushed at least `gap` apart, then moved up together if the last passed
    `bottom`."""
    out = list(ys)
    for k in range(1, len(out)):
        out[k] = max(out[k], out[k - 1] + gap)
    over = out[-1] - bottom if out else 0
    if over > 0:
        out = [y - over for y in out]
    return out


def at(xs: Sequence[float], ys: Sequence[float], x: float) -> float:
    """The polyline through (xs, ys), xs increasing, at x (flat past either end)."""
    if x <= xs[0]:
        return ys[0]
    if x >= xs[-1]:
        return ys[-1]
    k = bisect.bisect_right(xs, x)
    x0, x1, y0, y1 = xs[k - 1], xs[k], ys[k - 1], ys[k]
    return y0 if x1 == x0 else y0 + (y1 - y0) * (x - x0) / (x1 - x0)
