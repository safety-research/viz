"""Violin plots: each group's distribution as a mirrored density (a Gaussian kernel estimate, cut at the lowest and
highest values), with a slim box inside: the middle half as a thick line, 1.5 IQR whiskers and the median as a dot.
Vertical in the bars look by default.
"""
from __future__ import annotations

import math

from .. import scale as SC
from .. import svg as S
from .. import theme as th
from ..figure import Body, Figure
from .common import UNSET, as_set, resolve_unit, row_colors, series_colors
from .dist import cat_frame, dark, quantile, samples, summary_labels, tukey

LABEL = 12.5
GRID = 80  # density evaluated at this many points from the lowest value to the highest


def silverman(vals: list[float]) -> float:
    """Silverman's rule of thumb for the kernel width; 0 when the values are all the same."""
    n = len(vals)
    if n < 2:
        return 0.0
    m = sum(vals) / n
    sd = math.sqrt(sum((v - m) ** 2 for v in vals) / (n - 1))
    s = sorted(vals)
    iqr = quantile(s, 0.75) - quantile(s, 0.25)
    spread = min(sd, iqr / 1.34) if iqr > 0 else sd
    return 0.9 * spread * n ** -0.2


def density(vals: list[float], bandwidth: float) -> list[tuple[float, float]]:
    """(value, density) at GRID points from the lowest value to the highest. Above 2,000 values the kernel runs
    over 400 equal bins of them instead, which changes the curve by much less than a pixel."""
    lo, hi = min(vals), max(vals)
    n = len(vals)
    if n > 2000:
        k = 400
        w = (hi - lo) / k
        counts = [0] * k
        for v in vals:
            counts[min(int((v - lo) / w), k - 1)] += 1
        pts = [(lo + (i + 0.5) * w, c) for i, c in enumerate(counts) if c]
    else:
        pts = [(v, 1) for v in vals]
    c = 1 / (n * bandwidth * math.sqrt(2 * math.pi))
    grid = [lo + (hi - lo) * i / (GRID - 1) for i in range(GRID)]
    return [(g, c * sum(wt * math.exp(-0.5 * ((g - v) / bandwidth) ** 2) for v, wt in pts)) for g in grid]


def violin(data, *, series=None, color=None, colors=None, highlight=None, accent="intervention", scale="area",
           bandwidth=None, horizontal=False, domain=None, ticks=None, step=None, zero=None, unit=UNSET,
           decimals=None, fmt=None, signed=False, tick_format=None, values=True, ref=None, ref_label=None,
           ylabel=None, xlabel=None, height=None, grid=False,
           title=None, subtitle=None, legend=None, legend_position=None, width=None) -> Figure:
    """Violin plot per group: the distribution's shape, with a slim box and the median inside.

    data: {group: [values]}, a list of (group, [values]) pairs, or a DataFrame (one group per column);
          {group: [[series-1 values], [series-2 values]]} with series=[...] draws grouped violins. None and NaN are
          skipped.
    scale: "area" (default) gives every violin the same area, so a tighter distribution draws wider; "width" gives
    them all the same widest point. bandwidth: the kernel's standard deviation in data units (None uses
    Silverman's rule). The shape stops at the lowest and highest values.
    values=True writes each median beside its violin (above it when horizontal), formatted by decimals or fmt,
    when there is room and at most two series.
    horizontal=True puts the groups on the left as in hbar. ylabel (or xlabel when horizontal) titles the value
    axis. Values are percents by default (unit="" for scores, seconds, lengths); the axis starts at zero for
    percents unless zero=False. colors, color, highlight and accent work as in bars.
    """
    if scale not in ("area", "width"):
        raise ValueError("scale must be 'area' or 'width'")
    if bandwidth is not None and not bandwidth > 0:
        raise ValueError("bandwidth must be above 0")
    labels, vals, ns, _ = samples(data, series)
    names = list(series) if series is not None else None
    unit, unit_given = resolve_unit(unit)
    flat = [v for g in vals for s in g for v in s]
    SC.check_percent(flat, unit, unit_given)
    stats = [[tukey(s) if s else None for s in g] for g in vals]
    curves = []
    for g in vals:
        row = []
        for s in g:
            bw = bandwidth if bandwidth is not None else silverman(s)
            row.append(density(s, bw) if s and bw > 0 and max(s) > min(s) else None)
        curves.append(row)
    peak = max((d for row in curves for c in row if c for _, d in c), default=0.0)
    hl = as_set(highlight)
    zero_ = unit == "%" if zero is None else zero
    axis_title = (xlabel or ylabel) if horizontal else (ylabel or xlabel)
    fig = Figure(None, title=title, subtitle=subtitle, legend=legend, legend_position=legend_position,
                 width=width, kind="violin")

    def render(W: float) -> Body:
        n = len(labels)
        fmtv = SC.formatter(fmt, decimals, unit, signed, [s.median for g in stats for s in g if s])
        cols = series_colors(ns, colors if ns > 1 else None, names)
        single = row_colors(labels, color=color, colors=colors if ns == 1 else None, highlight=highlight,
                            accent=accent) if ns == 1 else None
        slot_h = 44.0 if ns == 1 else 30.0
        inner = ns * slot_h + (ns - 1) * 3
        roomy = horizontal and values and ns <= 2  # room above (and below) each violin for its median

        def slot_v(gw: float) -> float:
            return min(90.0 if n > 3 else 120.0, (gw * 0.8 - 3 * (ns - 1)) / ns)
        f = cat_frame(W, labels, ns, flat + ([ref] if ref is not None else []), horizontal=horizontal, unit=unit,
                      signed=signed, domain=domain, ticks=ticks, step=step, zero=zero_, tick_format=tick_format,
                      axis_title=axis_title, ref=ref, ref_label=ref_label, height=height, grid=grid,
                      bold=hl if ns == 1 else (), slot_v=slot_v, slot_h=slot_h,
                      row_height=inner + 2 * (LABEL + 6) if roomy else None, cat_lines=fig.meta.get("cat_lines", 0))
        out = list(f.svg)
        V = f.val
        half = f.slot / 2
        marks = []
        for i, gs in enumerate(stats):
            for j, st in enumerate(gs):
                if st is None:
                    continue
                c = single[i] if ns == 1 else cols[j]
                dk = dark(c)
                cc = f.center(i, j)
                curve = curves[i][j]
                bar = max(3.0, min(6.0, f.slot * 0.08))
                reach = bar / 2 + 3  # how far the violin reaches from its center line
                if curve:
                    top = peak if scale == "area" else max(d for _, d in curve)
                    side = [(V(v), half * d / top) for v, d in curve]
                    reach = max(reach, max(w for _, w in side))
                    pts = [f.xy(p, cc + w) for p, w in side] + [f.xy(p, cc - w) for p, w in reversed(side)]
                    d = "M" + " L".join(f"{S.n(x)},{S.n(y)}" for x, y in pts) + "Z"
                    out.append(S.path(d, c))
                out.append(f.seg(V(st.low), cc, V(st.high), cc, dk, 1.2))
                if abs(V(st.q3) - V(st.q1)) > 0.5:
                    out.append(f.seg(V(st.q1), cc, V(st.q3), cc, dk, bar))
                x, y = f.xy(V(st.median), cc)
                out.append(S.circle(x, y, max(2.5, bar * 0.6), th.BG, dk, 1.2))
                marks.append((i, j, V(st.median), reach, fmtv(st.median)))
        if values:
            beside = summary_labels(f, marks, ns, LABEL)
            if beside is not None:
                out += beside
        legend_items = list(zip(names, cols)) if ns > 1 and names else None
        return Body("".join(out), f.height, legend_items, meta=f.meta)

    fig.render = render
    return fig
