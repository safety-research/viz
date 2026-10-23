"""Tukey box plots: the median, the middle half of the values as a box, whiskers to the most extreme values within
1.5 times the box's height, and anything beyond as outlier dots. Vertical in the bars look by default.
"""
from __future__ import annotations

from .. import scale as SC
from .. import svg as S
from .. import text as T
from .. import theme as th
from ..figure import Body, Figure
from .common import UNSET, as_set, resolve_unit, row_colors, series_colors
from .dist import cat_frame, dark, dots, samples, summary_labels, swarm, tukey

LABEL = 12.5


def box(data, *, series=None, color=None, colors=None, highlight=None, accent="intervention", points=False,
        horizontal=False, domain=None, ticks=None, step=None, zero=None, unit=UNSET, decimals=None, fmt=None,
        signed=False, tick_format=None, values=True, ref=None, ref_label=None, ylabel=None, xlabel=None,
        height=None, box_width=None, grid=False,
        title=None, subtitle=None, legend=None, legend_position=None, frame=None, width=None) -> Figure:
    """Box plot per group (Tukey): median line, interquartile box, 1.5 IQR whiskers, outliers as dots.

    data: {group: [values]}, a list of (group, [values]) pairs, or a DataFrame (one group per column);
          {group: [[series-1 values], [series-2 values]]} with series=[...] draws grouped boxes. None and NaN are
          skipped.
    points=True overlays every value as a dot (a deterministic beeswarm) on a paler box.
    values=True writes each median beside its box at the median line (above the box when horizontal), formatted
    by decimals or fmt; with three or more series, or no room, it goes past the upper whisker instead.
    horizontal=True puts the groups on the left as in hbar. ylabel (or xlabel when horizontal) titles the value
    axis. Values are percents by default (unit="" for scores, seconds, lengths); the axis starts at zero for
    percents unless zero=False. colors, color, highlight and accent work as in bars.
    """
    labels, vals, ns, _ = samples(data, series)
    names = list(series) if series is not None else None
    unit, unit_given = resolve_unit(unit)
    flat = [v for g in vals for s in g for v in s]
    SC.check_percent(flat, unit, unit_given)
    stats = [[tukey(s) if s else None for s in g] for g in vals]
    hl = as_set(highlight)
    zero_ = unit == "%" if zero is None else zero
    axis_title = (xlabel or ylabel) if horizontal else (ylabel or xlabel)
    most = max((len(s) for g in vals for s in g), default=0)
    r_pt = 3.0 if most <= 40 else 2.4 if most <= 150 else 1.8
    r_out = 3.2
    fig = Figure(None, title=title, subtitle=subtitle, legend=legend, legend_position=legend_position,
                 frame=frame, width=width, kind="box")

    def render(W: float) -> Body:
        n = len(labels)
        fmtv = SC.formatter(fmt, decimals, unit, signed, [s.median for g in stats for s in g if s])
        cols = series_colors(ns, colors if ns > 1 else None, names)
        single = row_colors(labels, color=color, colors=colors if ns == 1 else None, highlight=highlight,
                            accent=accent) if ns == 1 else None

        def slot_v(gw: float) -> float:
            if box_width:
                return box_width
            cap = (22 if ns > 2 else 34 if ns == 2 else 46) * (1.5 if n <= 3 and W >= 520 else 1)
            return min(cap, gw * (0.25 if ns > 2 else 0.36 if ns == 2 else 0.5))
        slot_h = box_width or (14 if ns > 2 else 18 if ns == 2 else 24)
        inner = ns * slot_h + (ns - 1) * 3

        def frame_(ends=(), roomy=False):
            return cat_frame(W, labels, ns, flat + ([ref] if ref is not None else []), horizontal=horizontal,
                             unit=unit, signed=signed, domain=domain, ticks=ticks, step=step, zero=zero_,
                             tick_format=tick_format, axis_title=axis_title, ref=ref, ref_label=ref_label,
                             height=height, grid=grid, bold=hl if ns == 1 else (), slot_v=slot_v, slot_h=slot_h,
                             row_height=inner + 2 * (LABEL + 6) if roomy else None, ends=ends,
                             cat_lines=fig.meta.get("cat_lines", 0))

        f = frame_(roomy=horizontal and values and ns <= 2)
        beside = None
        if values:
            marks = [(i, j, f.val(st.median), f.slot / 2, fmtv(st.median))
                     for i, gs in enumerate(stats) for j, st in enumerate(gs) if st]
            beside = summary_labels(f, marks, ns, LABEL)
            if beside is None and horizontal:  # past the upper whisker instead: leave room on the right
                f = frame_([(max(s), T.width(fmtv(st.median), LABEL) + 10 + r_out)
                            for g, gs in zip(vals, stats) for s, st in zip(g, gs) if st])
        out = list(f.svg)
        labels_svg = list(beside or [])
        V = f.val
        for i, gs in enumerate(stats):
            for j, st in enumerate(gs):
                if st is None:
                    continue
                c = single[i] if ns == 1 else cols[j]
                dk = dark(c)
                cc, half = f.center(i, j), f.slot / 2
                cap = half * 0.5
                for a, b in ((st.low, st.q1), (st.q3, st.high)):
                    if abs(V(a) - V(b)) > 0.5:
                        out.append(f.seg(V(a), cc, V(b), cc, dk, 1.5))
                for w in (st.low, st.high):
                    out.append(f.seg(V(w), cc - cap, V(w), cc + cap, dk, 1.5))
                a, b = V(st.q1), V(st.q3)
                if abs(a - b) < 2:  # an empty box still shows as a sliver
                    m = V(st.median)
                    a, b = m - 1, m + 1
                out.append(f.rect(a, b, cc - half, cc + half, th.mix(c, th.BG, 0.55) if points else c))
                out.append(f.seg(V(st.median), cc - half, V(st.median), cc + half, dk if points else th.BG, 2.5))
                vs = vals[i][j]
                if points:
                    out.append(dots([V(u) for u in vs], cc, half, r_pt, dk, f.horizontal, 0.8 if r_pt >= 2.4 else 0.5))
                elif st.outliers:
                    pos = [V(u) for u in st.outliers]
                    for p, o in sorted(zip(pos, swarm(pos, r_out + 0.6, half - r_out))):
                        x, y = f.xy(p, cc + o)
                        out.append(S.circle(x, y, r_out, th.BG, dk, 1.4))
                if values and beside is None:  # past the upper whisker and any dot beyond it
                    beyond = [u for u in (vs if points else st.outliers) if u >= st.high]
                    r_end = (r_pt if points else r_out) + 1
                    edge = V(st.high)
                    if f.horizontal:
                        if beyond:
                            edge = max(edge, V(max(beyond)) + r_end)
                        labels_svg.append(S.text(edge + 8, cc + LABEL * 0.36, fmtv(st.median), LABEL, th.INK2,
                                                 halo=th.BG))
                    else:
                        if beyond:
                            edge = min(edge, V(max(beyond)) - r_end)
                        labels_svg.append(S.text(cc, edge - 6, fmtv(st.median), LABEL, th.INK2, "middle", halo=th.BG))
        out += labels_svg
        legend_items = list(zip(names, cols)) if ns > 1 and names else None
        return Body("".join(out), f.height, legend_items, meta=f.meta)

    fig.render = render
    return fig
