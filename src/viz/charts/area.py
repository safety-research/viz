"""Stacked areas over x: how a total, or each x's shares, split across checkpoints or steps. Each band is named at
its right end, inside the band when it is tall enough there and beside it otherwise, instead of with a legend."""
from __future__ import annotations

from .. import scale as SC
from .. import svg as S
from .. import text as T
from .. import theme as th
from ..figure import Body, Figure
from . import axis as A
from .common import UNSET, plot_height, resolve_unit, series_colors
from .line import _series

LABEL = 12.5  # band names, the size of line's end labels
ROOM = 18     # px a band needs at its right end, under its whole name, to hold the name inside


def _stack(series, x=None, normalize: bool = False) -> tuple[list[str], list[float], list[list[float]]]:
    """(names, xs, values): values[i][j] is series i at the j-th x, in x order. None and NaN count as 0;
    normalize=True turns each x's values into percents of their total."""
    data = _series(series, x)
    if not data:
        raise ValueError("area needs at least one series")
    names = list(data)
    xs = [a for a, _ in data[names[0]]]
    if not xs:
        raise ValueError(f"series {names[0]!r} has no values")
    for nm in names[1:]:
        if [a for a, _ in data[nm]] != xs:
            raise ValueError(f"series {nm!r} has other x values than {names[0]!r}; stacked areas share one x")
    order = sorted(range(len(xs)), key=lambda j: xs[j])
    vals = [[data[nm][j][1] or 0.0 for j in order] for nm in names]
    for nm, row in zip(names, vals):
        if any(v < 0 for v in row):
            raise ValueError(f"series {nm!r} has a value below 0; stacked areas need values of 0 or more")
    if normalize:
        for j in range(len(order)):
            total = sum(row[j] for row in vals)
            for row in vals:
                row[j] = 100 * row[j] / total if total else 0.0
    return names, [xs[j] for j in order], vals


def area(series, *, x=None, normalize=False, colors=None, xscale="linear", xticks=None, xtick_labels=None, xunit="",
         xlabel=None, ylabel=None, ticks=None, domain=None, step=None, unit=UNSET, decimals=None, fmt=None,
         height=None, marks=None, end_labels=True,
         title=None, subtitle=None, legend=False, legend_position=None, frame=None, width=None) -> Figure:
    """Stacked area chart, the first series at the bottom.

    series: {name: [y, ...]} with a shared x=[...] (or {name: [(x, y), ...]} or {name: {x: y}} with the same x values
    in every series). None and NaN count as 0; values below 0 are an error. normalize=True turns each x into shares
    of its total (0-100%).
    Each band is named at its right end: inside the band where it is tall enough, else beside it. Colors follow the
    color roles (viz.set_roles), else orange, blue, sage, ...; colors= (a list, {name: color} or role names)
    overrides them, such as ["blue", "beige", "coral"] for good, neutral and bad outcomes.
    The axes take line()'s options: xscale ("linear", "category" or "log"), xticks, xtick_labels, xunit, xlabel,
    ylabel, ticks, domain, step, unit (percent by default; unit="" for counts), height and marks={x: "label"}.
    decimals and fmt set the numbers in the alt text.
    """
    A.check_xscale(xscale)
    names, xs, vals = _stack(series, x, normalize)
    unit, given = resolve_unit(unit)
    if not normalize:
        SC.check_percent([v for row in vals for v in row], unit, given)
    if xscale == "log" and min(xs) <= 0:
        raise ValueError("xscale='log' needs x values above 0")
    xticks = list(xticks) if xticks is not None else None
    xs_all = sorted(set(xs))
    mark_list = A.read_marks(marks)
    A.check_marks(mark_list, xscale, xs_all + (xticks or []))
    mark_xs = [m for m, _ in mark_list]
    tops: list[list[float]] = []  # the top of each band: the running sum, bottom series first
    for row in vals:
        tops.append([a + b for a, b in zip(tops[-1], row)] if tops else list(row))
    n = len(names)

    def render(W: float) -> Body:
        H = height or plot_height()
        cols = series_colors(n, colors, names)
        if ticks is not None:
            lo, hi, tk = min(ticks), max(ticks), list(ticks)
        elif domain is not None:
            lo, hi, tk = SC.domain(tops[-1], domain[0], domain[1], unit == "%", step=step)
        elif normalize:
            lo, hi, tk = 0.0, 100.0, [0, 25, 50, 75, 100]
        else:
            lo, hi, tk = SC.domain(tops[-1], percent=unit == "%", step=step)
        tfmt = SC.tick_formatter(tk, unit)
        xt = A.x_ticks(xs_all, xticks, xscale, xtick_labels, mark_xs)
        xlab = A.x_labeler(xtick_labels, xt, xunit, xscale)
        PL = max(T.width(tfmt(t), th.TICK_SIZE) for t in tk) + 14 + (18 if ylabel else 0)
        PB = 30 + (22 if xlabel else 0)
        widths = [T.width(nm, LABEL, "sans", 600) for nm in names]

        def room(i: int) -> float | None:
            """The middle of the free space under band i's name at its right end, or None when it doesn't fit."""
            right = pxs[-1] - 6
            left = right - widths[i]
            if left < PL + 4:
                return None
            upper = [Y(v) for v in tops[i]]
            lower = [Y(v) for v in tops[i - 1]] if i else [Y(0.0)] * len(pxs)
            probes = [left, right] + [p for p in pxs if left < p < right]
            top = max(A.at(pxs, upper, p) for p in probes)
            bottom = min(A.at(pxs, lower, p) for p in probes)
            return (top + bottom) / 2 if bottom - top >= ROOM else None

        beside: set[int] = set()  # names outside the plot need a right margin, which narrows the plot: settle both
        while True:
            PR = (max(widths[i] for i in beside) + 16) if beside else 12
            PW = W - PL - PR
            X = A.x_scale(xscale, xt, xs_all, PL, PW, mark_xs)
            placed, rows = A.mark_layout(mark_list, X, 0, W)
            PT = 12 + A.MARK_ROW * rows
            PH = H - PT - PB
            Y = lambda v, PT=PT, PH=PH: PT + PH * (1 - (min(max(v, lo), hi) - lo) / (hi - lo))
            pxs = [X(a) for a in xs]
            inside = {i: y for i in range(n) if i not in beside and (y := room(i)) is not None} if end_labels else {}
            more = {i for i in range(n) if i not in inside} if end_labels else set()
            if more <= beside:
                break
            beside |= more
        out = []
        for t in tk:
            out.append(S.line(PL, Y(t), PL + PW, Y(t), th.AXIS if t == lo else th.GRID))
            out.append(S.text(PL - 10, Y(t) + 4, tfmt(t), th.TICK_SIZE, th.MUTED, "end"))
        for t in xt:
            out.append(A.tick_text(X(t), PT + PH + 20, t, "middle", xlab, xscale == "log" and xtick_labels is None))
        if xlabel:
            out.append(S.text(PL + PW / 2, PT + PH + 44, xlabel, 12.5, th.INK2, "middle"))
        if ylabel:
            out.append(S.rotated(13, PT + PH / 2, ylabel, size=12))
        for i in range(n):  # each band from the top of the one below to its own top
            upper = [f"{S.n(p)},{S.n(Y(v))}" for p, v in zip(pxs, tops[i])]
            lower = [f"{S.n(p)},{S.n(Y(v))}" for p, v in zip(pxs, tops[i - 1] if i else [0.0] * len(pxs))]
            out.append(f'<polygon points="{" ".join(upper + lower[::-1])}" fill="{cols[i]}"/>')
        for i in range(n - 1):  # a thin line of background between neighbouring bands
            d = "M" + " L".join(f"{S.n(p)},{S.n(Y(v))}" for p, v in zip(pxs, tops[i]))
            out.append(S.path(d, "none", th.BG, 1, extra='stroke-linejoin="round"'))
        out.append(A.mark_lines(mark_list, X, PT, PT + PH, th.INK2))  # over the bands, which cover the plot
        out.append(A.mark_labels(placed, PT))
        for i, yy in inside.items():
            out.append(S.text(pxs[-1] - 6, yy + 4.5, names[i], LABEL, th.text_on(cols[i]), "end", 600))
        outside = sorted((((Y(tops[i][-1]) + Y(tops[i - 1][-1] if i else 0.0)) / 2), i) for i in beside)
        for (_, i), yy in zip(outside, A.spread([y for y, _ in outside], 15, PT + PH)):
            out.append(S.text(PL + PW + 8, yy + 4.5, names[i], LABEL, th.readable(cols[i]), "start", 600))
        return Body("".join(out), H, list(zip(names, cols)), "square", meta={"plot_x": (PL, PL + PW)})

    return Figure(render, title=title, subtitle=subtitle, legend=legend, legend_position=legend_position,
                  frame=frame, width=width, kind="area")
