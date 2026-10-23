"""Strip plot: one dot per item or run in each group, laid out as a deterministic beeswarm so no dot hides another,
with the mean as a short ink line and an optional interval. Vertical in the bars look by default.
"""
from __future__ import annotations

from collections.abc import Mapping

from .. import scale as SC
from .. import svg as S
from .. import text as T
from .. import theme as th
from ..figure import Body, Figure
from .common import UNSET, as_set, resolve_unit, row_colors, series_colors
from .dist import cat_frame, dark, is_seq, mean_ci, samples, summary_labels, swarm
from .dist import mean as average

LABEL = 12.5


def _intervals(ci, labels: list[str], vals: list[list[list[float]]], ns: int):
    """ci: True (95% t interval of each mean), {label: (lo, hi)}, {label: [(lo, hi), ...]} or a list per group."""
    if ci is None or ci is False:
        return [[None] * ns for _ in labels]
    if ci is True:
        return [[mean_ci(s) for s in g] for g in vals]
    if isinstance(ci, Mapping):
        seq = [ci.get(lab) for lab in labels]
    else:
        seq = list(ci)
        if len(seq) != len(labels):
            raise ValueError(f"ci has {len(seq)} entries for {len(labels)} groups")
    out = []
    for c in seq:
        if c is None:
            out.append([None] * ns)
        elif ns == 1 and len(c) == 2 and not is_seq(c[0]):
            out.append([(float(c[0]), float(c[1]))])
        else:
            out.append([None if x is None else (float(x[0]), float(x[1])) for x in c])
    return out


def strip(data, *, series=None, color=None, colors=None, highlight=None, accent="intervention", mean=True, ci=None,
          horizontal=False, domain=None, ticks=None, step=None, zero=None, unit=UNSET, decimals=None, fmt=None,
          signed=False, tick_format=None, values=True, ref=None, ref_label=None, ylabel=None, xlabel=None,
          dot_size=None, height=None, grid=False,
          title=None, subtitle=None, legend=None, legend_position=None, width=None) -> Figure:
    """Strip plot: every item or run as a dot per group, the mean as an ink line, an optional interval.

    data: {group: [values]}, a list of (group, [values]) pairs, or a DataFrame (one group per column);
          {group: [[series-1 values], [series-2 values]]} with series=[...] puts several strips in a group.
          None and NaN are skipped.
    mean=False drops the mean line. ci: True for a 95% t interval of each mean, or {group: (lo, hi)} /
    {group: [(lo, hi), ...]} given. values=True writes each mean beside its mean line (above it when horizontal),
    formatted by decimals or fmt; with three or more series, or no room, it goes past the strip's top dot
    instead. horizontal=True puts the groups on the left as in hbar. ylabel (or xlabel when horizontal) titles the
    value axis. Values are percents by default (unit="" for scores); the axis starts at zero for percents unless
    zero=False. colors, color, highlight and accent work as in bars.
    """
    labels, vals, ns, _ = samples(data, series)
    names = list(series) if series is not None else None
    unit, unit_given = resolve_unit(unit)
    flat = [v for g in vals for s in g for v in s]
    SC.check_percent(flat, unit, unit_given)
    cis = _intervals(ci, labels, vals, ns)
    means = [[average(s) if s else None for s in g] for g in vals]
    hl = as_set(highlight)
    zero_ = unit == "%" if zero is None else zero
    axis_title = (xlabel or ylabel) if horizontal else (ylabel or xlabel)
    most = max((len(s) for g in vals for s in g), default=0)
    r = dot_size or (4.5 if most <= 30 else 3.5 if most <= 100 else 2.5)
    fig = Figure(None, title=title, subtitle=subtitle, legend=legend, legend_position=legend_position,
                 width=width, kind="strip")

    def render(W: float) -> Body:
        fmtv = SC.formatter(fmt, decimals, unit, signed, [m for g in means for m in g if m is not None])
        show = values and mean
        cols = series_colors(ns, colors if ns > 1 else None, names)
        single = row_colors(labels, color=color, colors=colors if ns == 1 else None, highlight=highlight,
                            accent=accent) if ns == 1 else None
        ext = flat + [x for g in cis for c in g if c for x in c] + ([ref] if ref is not None else [])
        slot_h = max(6 * r, 26.0) if ns == 1 else max(4 * r, 18.0)
        inner = ns * slot_h + (ns - 1) * 3

        def frame_(ends=(), roomy=False):
            return cat_frame(W, labels, ns, ext, horizontal=horizontal, unit=unit, signed=signed, domain=domain,
                             ticks=ticks, step=step, zero=zero_, tick_format=tick_format, axis_title=axis_title,
                             ref=ref, ref_label=ref_label, height=height, grid=grid, bold=hl if ns == 1 else (),
                             slot_v=lambda gw: min(120.0, (gw * 0.75 - 3 * (ns - 1)) / ns), slot_h=slot_h,
                             row_height=inner + 2 * (LABEL + 6) if roomy else None, ends=ends,
                             cat_lines=fig.meta.get("cat_lines", 0))

        def swarms(f):  # (group, series, dot positions, offsets, half-length of the mean line)
            out_ = []
            for i, g in enumerate(vals):
                for j, s in enumerate(g):
                    if s:
                        pos = [f.val(u) for u in s]
                        offs = swarm(pos, r, f.slot / 2 - r - 0.5)
                        reach = min(f.slot / 2, max(max(abs(o) for o in offs) + r + 7, 13.0))
                        out_.append((i, j, pos, offs, reach))
            return out_

        f = frame_(roomy=horizontal and show and ns <= 2)
        marks = swarms(f)
        beside = None
        if show:
            beside = summary_labels(f, [(i, j, f.val(means[i][j]), reach, fmtv(means[i][j]))
                                        for i, j, _, _, reach in marks], ns, LABEL)
            if beside is None and horizontal:  # right of each strip instead: leave room for the labels
                f = frame_([(max(vals[i][j] + ([cis[i][j][1]] if cis[i][j] else [])),
                             T.width(fmtv(means[i][j]), LABEL) + 10 + r) for i, j, *_ in marks])
                marks = swarms(f)
        out = list(f.svg)
        labels_svg = list(beside or [])
        V = f.val
        for i, j, pos, offs, reach in marks:
            s = vals[i][j]
            c = single[i] if ns == 1 else cols[j]
            cc, half = f.center(i, j), f.slot / 2
            for p, o in sorted(zip(pos, offs)):
                x, y = f.xy(p, cc + o)
                out.append(S.circle(x, y, r, c, th.BG, 1))
            m, iv = means[i][j], cis[i][j]
            ink = th.INK if (not hl or ns > 1 or labels[i] in hl) else dark(c)
            if iv:  # over the dots, as in the usual mean-and-interval scatter plots
                tick = min(4.0, half)
                out.append(f.seg(V(iv[0]), cc, V(iv[1]), cc, ink, 1.5))
                for e in iv:
                    out.append(f.seg(V(e), cc - tick, V(e), cc + tick, ink, 1.5))
            if mean:
                out.append(f.seg(V(m), cc - reach, V(m), cc + reach, ink, 2.5, cap="round"))
            if show and beside is None:  # past the strip's top dot or interval
                if f.horizontal:
                    edge = max(V(max(s)) + r + 1, V(iv[1]) if iv else 0)
                    labels_svg.append(S.text(edge + 8, cc + LABEL * 0.36, fmtv(m), LABEL, th.INK2, halo=th.BG))
                else:
                    edge = min(V(max(s)) - r - 1, V(iv[1]) if iv else 1e9)
                    labels_svg.append(S.text(cc, edge - 6, fmtv(m), LABEL, th.INK2, "middle", halo=th.BG))
        out += labels_svg
        legend_items = list(zip(names, cols)) if ns > 1 and names else None
        return Body("".join(out), f.height, legend_items, "round", meta=f.meta)

    fig.render = render
    return fig
