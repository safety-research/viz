"""Lines over steps or doses, labeled at their ends instead of with a legend box."""
from __future__ import annotations

import math
import numbers
from collections.abc import Mapping

from .. import scale as SC
from .. import svg as S
from .. import text as T
from .. import theme as th
from ..figure import Body, Figure
from . import axis as A
from .common import UNSET, as_set, plot_height, resolve_unit, series_colors


def _y(v) -> float | None:
    """A y value as a float; None and NaN are missing."""
    if v is None:
        return None
    f = float(v)
    return None if math.isnan(f) else f


def _series(series, x):
    out = {}
    for name, ys in series.items():
        if isinstance(ys, Mapping):
            pts = [(float(k), _y(v)) for k, v in ys.items()]
        else:
            ys = list(ys)
            if ys and isinstance(ys[0], (list, tuple)):
                pts = [(float(a), _y(b)) for a, b in ys]
            else:
                if x is None:
                    xs = list(range(len(ys)))
                else:
                    xs = list(x)
                    if len(xs) != len(ys):
                        raise ValueError(f"series {name!r} has {len(ys)} values for {len(xs)} x positions")
                pts = [(float(a), _y(b)) for a, b in zip(xs, ys)]
        out[str(name)] = pts
    return out


def smoothed(pts: list[tuple[float, float | None]], weight: float) -> list[tuple[float, float | None]]:
    """TensorBoard's smoothing of (x, y) points: an exponential moving average with this weight, divided by
    1 - weight^n after n values so it doesn't start pulled toward zero. Missing values stay missing and don't count;
    a constant series stays as it is, and weight 0 changes nothing."""
    ys = [y for _, y in pts if y is not None]
    if not ys or all(y == ys[0] for y in ys):
        return list(pts)
    out, last, n = [], 0.0, 0
    for x, y in pts:
        if y is None:
            out.append((x, None))
            continue
        last = last * weight + (1 - weight) * y
        n += 1
        out.append((x, last / (1 - weight ** n)))
    return out


def check_smooth(smooth) -> None:
    if smooth is None:
        return
    if isinstance(smooth, bool) or not isinstance(smooth, numbers.Real) or not 0 <= smooth < 1:
        raise ValueError(f"smooth={smooth!r}: give TensorBoard's smoothing weight, a number from 0 up to (not "
                         "including) 1, such as 0.9")


def line(series, *, x=None, colors=None, highlight=None, domain=None, ticks=None, step=None, xticks=None,
         xtick_labels=None, unit=UNSET, xunit="", decimals=None, fmt=None, xlabel=None, ylabel=None, bands=None,
         runs=None, markers=None, end_labels=True, end_values=True, ref=None, ref_label=None, height=None, zero=True,
         xscale="linear", yscale="linear", smooth=None, marks=None,
         title=None, subtitle=None, legend=False, legend_position=None, frame=None, width=None) -> Figure:
    """Line chart.

    series: {name: [y, ...]} with a shared x=[...]; or {name: [(x, y), ...]}; or {name: {x: y}}.
    bands: {name: ([lo...], [hi...])} shaded intervals. highlight: name(s) keep their color, others go gray.
    runs: {name: [run, run, ...]} draws each run (training seed) as a thin faint line under the bold line of that
    name, which shows their mean or median. Each run takes the forms a series does: [y, ...] on the shared x,
    [(x, y), ...] or {x: y}.
    xtick_labels: {x: "label"} (e.g. {0: "0", 1e6: "1M"}) or a list matching xticks.
    xscale: "linear", "category" (x values evenly spaced in order, e.g. doses 0, 1M, 3M, 10M) or "log". A linear axis
    with more than 12 x values ticks at round steps.
    yscale: "linear" or "log": ticks at each power of ten, or at 1, 2, 3, ... or 1, 2, 5 times one when the values
    span less (a loss from 2.1 to 4.4 ticks at 2, 3, 4, 5). Every y value must be above 0.
    smooth: TensorBoard's smoothing weight, from 0 up to 1 (0.9 smooths a noisy reward curve): each series is drawn
    bold as an exponential moving average of its values, debiased so it starts at the first value, over its raw
    values as a thin faint line (a series with runs= keeps its raw runs instead). End labels and values give the
    smoothed values; the y axis still covers the raw ones. Markers are off by default when smoothing.
    marks: {x: "label"} draws a thin dashed vertical line at each x with its label above the plot, such as
    {500: "RL starts", 1500: "Checkpoint we chose"}.
    """
    A.check_xscale(xscale)
    if yscale not in ("linear", "log"):
        raise ValueError(f"yscale={yscale!r}: use 'linear' or 'log'")
    check_smooth(smooth)
    xticks = list(xticks) if xticks is not None else None
    data = _series(series, x)
    names = list(data)
    run_data: dict[str, list[list[tuple[float, float | None]]]] = {}
    for nm, rs in (runs or {}).items():
        if str(nm) not in data:
            raise ValueError(f"runs for {nm!r}, which is not one of the series")
        run_data[str(nm)] = [[(a, None if b is None or math.isnan(b) else b) for a, b in pts]
                             for pts in _series(dict(enumerate(rs)), x).values()]
    unit, _ = resolve_unit(unit)
    hl = as_set(highlight)
    cols = series_colors(len(names), colors, names, highlight=highlight)
    yvals = [v for pts in data.values() for _, v in pts if v is not None]
    if bands:
        for lo_, hi_ in bands.values():
            yvals += [v for v in list(lo_) + list(hi_) if v is not None]
    yvals += [v for rs in run_data.values() for pts in rs for _, v in pts if v is not None]
    xs_all = sorted({p[0] for pts in data.values() for p in pts} | {p[0] for rs in run_data.values() for pts in rs for p in pts})
    mark_list = A.read_marks(marks)
    A.check_marks(mark_list, xscale, xs_all + (xticks or []))
    if yscale == "log":
        low = [v for v in yvals + ([ref] if ref is not None else []) if v <= 0]
        if low:
            raise ValueError(f"yscale='log' needs y values above 0, got {low[0]:g}")
    smoothing = bool(smooth)  # 0 leaves every value as it is
    shown = {nm: smoothed(pts, smooth) for nm, pts in data.items()} if smoothing else data
    draw_markers = (not smoothing) if markers is None else markers

    def render(W: float) -> Body:
        H = height or plot_height()
        fmtv = SC.formatter(fmt, decimals, unit, False, yvals)
        extent = yvals + ([ref] if ref is not None else [])
        log_y = yscale == "log"
        if log_y:
            lo, hi, tk = A.log_axis(extent, ticks, domain)
            tfmt = lambda t: A.log_text(t, unit)
        else:
            if ticks is not None:
                lo, hi, tk = min(ticks), max(ticks), list(ticks)
            elif domain is not None:
                lo, hi, tk = SC.domain(extent, domain[0], domain[1], unit == "%", step=step)
            else:
                lo, hi, tk = SC.domain(extent, percent=unit == "%", zero=zero, step=step)
            tfmt = SC.tick_formatter(tk, unit)
        xt = A.x_ticks(xs_all, xticks, xscale, xtick_labels, [m for m, _ in mark_list])
        xlab = A.x_labeler(xtick_labels, xt, xunit, xscale)
        PL = max(A.tick_width(t, tfmt, log_y, unit) for t in tk) + 14 + (18 if ylabel else 0)
        end_w = 0.0
        if end_labels:
            for nm, pts in shown.items():
                have = [p for p in pts if p[1] is not None]
                if have:
                    s = nm + (f"  {fmtv(have[-1][1])}" if end_values else "")
                    end_w = max(end_w, T.width(s, 12.5, "sans", 600))
        PR = (end_w + 16) if end_labels else 12
        PB = 30 + (22 if xlabel else 0)
        PW = W - PL - PR
        X = A.x_scale(xscale, xt, xs_all, PL, PW, [m for m, _ in mark_list])
        placed, rows = A.mark_layout(mark_list, X, 0, W)
        PT = 12 + A.MARK_ROW * rows
        PH = H - PT - PB
        if log_y:
            la, lb = math.log(lo), math.log(hi)
            Y = lambda v: PT + PH * (1 - (math.log(min(max(v, lo), hi)) - la) / (lb - la))
        else:
            Y = lambda v: PT + PH * (1 - (min(max(v, lo), hi) - lo) / (hi - lo))
        out = []
        if log_y and lo not in tk:
            out.append(S.line(PL, Y(lo), PL + PW, Y(lo), th.AXIS))
        for t in tk:
            out.append(S.line(PL, Y(t), PL + PW, Y(t), th.AXIS if t == lo else th.GRID))
            out.append(A.tick_text(PL - 10, Y(t) + 4, t, "end", tfmt, log_y, unit))
        for t in xt:
            out.append(A.tick_text(X(t), PT + PH + 20, t, "middle", xlab, xscale == "log" and xtick_labels is None))
        if xlabel:
            out.append(S.text(PL + PW / 2, PT + PH + 44, xlabel, 12.5, th.INK2, "middle"))
        if ylabel:
            out.append(S.rotated(13, PT + PH / 2, ylabel, size=12))
        out.append(A.mark_lines(mark_list, X, PT, PT + PH, th.MUTED))
        out.append(A.mark_labels(placed, PT))
        if ref is not None:
            out.append(S.line(PL, Y(ref), PL + PW, Y(ref), th.MUTED, 1, "4 4"))
            if ref_label:
                out.append(S.text(PL + 6, Y(ref) - 6, ref_label, th.MIN_TEXT, th.MUTED))
        order = [i for i, nm in enumerate(names) if hl and nm not in hl] + [i for i, nm in enumerate(names) if not hl or nm in hl]
        for i in order:
            nm, c = names[i], cols[i]
            if bands and nm in bands:
                blo, bhi = bands[nm]
                xs_ = [p[0] for p in data[nm]]
                top = " ".join(f"{S.n(X(a))},{S.n(Y(b))}" for a, b in zip(xs_, bhi) if b is not None)
                bot = " ".join(f"{S.n(X(a))},{S.n(Y(b))}" for a, b in reversed(list(zip(xs_, blo))) if b is not None)
                out.append(f'<polygon points="{top} {bot}" fill="{c}" fill-opacity="0.16"/>')
        for i in order:  # runs, and the raw values of a smoothed series: thin and faint, under every bold line
            faint = run_data.get(names[i], [])
            if smoothing and names[i] not in run_data:
                faint = [data[names[i]]]
            for pts in faint:
                pts = [(a, b) for a, b in pts if b is not None]
                if len(pts) > 1:
                    d = "M" + " L".join(f"{S.n(X(a))},{S.n(Y(b))}" for a, b in pts)
                    out.append(f'<path d="{d}" fill="none" stroke="{cols[i]}" stroke-width="1.2" stroke-opacity="0.4" '
                               f'stroke-linejoin="round" stroke-linecap="round"/>')
        ends = []
        for i in order:
            nm, c = names[i], cols[i]
            pts = [(a, b) for a, b in shown[nm] if b is not None]
            if not pts:
                continue
            d = "M" + " L".join(f"{S.n(X(a))},{S.n(Y(b))}" for a, b in pts)
            sw = 2.25 if (not hl or nm in hl) else 1.6
            out.append(f'<path d="{d}" fill="none" stroke="{c}" stroke-width="{sw}" stroke-linejoin="round" stroke-linecap="round"/>')
            if draw_markers:
                for a, b in pts:
                    out.append(S.circle(X(a), Y(b), 3.6, c, th.BG, 1.5))
            ends.append([Y(pts[-1][1]), nm, c, pts[-1][1]])
        if end_labels and ends:
            ends.sort(key=lambda e: e[0])
            for e, yy in zip(ends, A.spread([e[0] for e in ends], 15, PT + PH)):  # apart, then back inside the plot
                e[0] = yy
            for yy, nm, c, v in ends:
                ink = th.readable(c)  # the series color, darkened only as far as 4.5:1 needs
                parts = [(nm, {"size": 12.5, "weight": 600, "fill": ink})]
                if end_values:
                    parts.append((fmtv(v), {"size": 12.5, "fill": th.INK2, "dx": 6}))
                out.append(S.spans(PL + PW + 10, yy + 4.5, parts))
        return Body("".join(out), H, list(zip(names, cols)), "line")

    return Figure(render, title=title, subtitle=subtitle, legend=legend,
                  legend_position=legend_position, frame=frame, width=width, kind="line")
