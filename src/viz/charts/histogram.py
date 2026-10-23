"""Histogram: one distribution as solid bars, or up to three overlaid as translucent fills with crisp outlines.

Bins are deterministic: the Freedman-Diaconis width rounded to a 1, 2, 2.5 or 5 width (whole-number data gets
whole-number bins centered on its values), a number of equal bins, or explicit edges. Overlaid groups share one set
of bins and are labeled directly above the bins where each stands out, or with a legend when no spot is free.
"""
from __future__ import annotations

import math
from collections.abc import Mapping

from .. import scale as SC
from .. import svg as S
from .. import text as T
from .. import theme as th
from ..figure import Body, Figure
from .common import series_colors
from .dist import LABEL_SIZE, bin_counts, bin_edges, free_spot, key_label, key_width, samples, whole


def histogram(data, *, bins=None, stat="count", color=None, colors=None, domain=None, ticks=None, step=None,
              unit="", tick_format=None, decimals=None, fmt=None, values=False, ref=None, ref_label=None,
              xlabel=None, ylabel=None, yticks=None, height=None,
              title=None, subtitle=None, legend=None, legend_position=None, frame=None, width=None) -> Figure:
    """Histogram of one distribution, or of up to three overlaid.

    data: a list of numbers, {name: [numbers]} for overlaid groups, a pandas Series, or a DataFrame (one group per
          column). None and NaN are skipped.
    bins: None (Freedman-Diaconis, rounded to a nice width), a number of equal bins, or a list of edges.
    stat: "count" (default) or "percent" of each group's items, which compares groups of different sizes.
    domain: (lo, hi) of the x axis; values outside it are left out of the bars but still count in percents.
    The x values are plain numbers by default (unit="" ; unit="%" for rates); ticks, step and tick_format set the
    x axis, yticks the y axis. values=True writes each bar's count or percent (one distribution only), formatted by
    decimals or fmt. ref: a dashed vertical line, ref_label its label. A legend replaces the direct labels of
    overlaid groups when legend=True or when they don't fit.
    """
    if stat not in ("count", "percent"):
        raise ValueError("stat must be 'count' or 'percent'")
    unit = "" if unit is None else str(unit)
    labels, vals, ns, _ = samples(data, flat_label="")
    if ns != 1:
        raise ValueError("histogram data: a list of numbers or {name: [numbers]}, one list per group")
    groups = [g[0] for g in vals]
    ng = len(groups)
    names = labels
    lo_d, hi_d = (float(domain[0]), float(domain[1])) if domain is not None else (None, None)
    inside = [[v for v in g if domain is None or lo_d <= v <= hi_d] for g in groups]
    pooled = [v for g in inside for v in g]
    span = (lo_d, hi_d) if domain is not None else None
    edges = bin_edges(pooled, bins, span)
    centered = bins is None and whole(pooled) and edges[1] - edges[0] == 1  # one bar per whole number
    counts = [bin_counts(g, edges) for g in inside]
    if stat == "percent":
        heights = [[100 * c / len(g) if g else 0.0 for c in cs] for cs, g in zip(counts, groups)]
    else:
        heights = [[float(c) for c in cs] for cs in counts]
    cols = series_colors(ng, colors if colors is not None else color, names)
    yunit = "%" if stat == "percent" else ""
    named = [nm for nm in names if nm]
    want_legend = legend is True or isinstance(legend, (Mapping, list, tuple))

    def render(W: float) -> Body:
        H = height or 320
        top_h = max((h for hs in heights for h in hs), default=0.0)
        # ---- y axis: counts get whole-number ticks
        if yticks is not None:
            ylo, yhi, ytk = min(yticks), max(yticks), list(yticks)
        else:
            ylo, yhi, ytk = SC.domain([top_h or 1.0], percent=stat == "percent")
            if stat == "count" and len(ytk) > 1 and ytk[1] - ytk[0] < 1:
                ylo, yhi, ytk = SC.domain([top_h or 1.0], step=1)
        yfmt = SC.tick_formatter(ytk, yunit)
        # ---- x axis: covers the bins and the domain
        if ticks is not None:
            xt = list(ticks)
            xlo, xhi = min(xt + [edges[0]]), max(xt + [edges[-1]])
        else:
            a = min(edges[0], lo_d) if domain is not None else edges[0]
            b = max(edges[-1], hi_d) if domain is not None else edges[-1]
            if ref is not None:
                a, b = min(a, ref), max(b, ref)
            st = step or SC.nice_step(b - a, 5)
            if centered and not step:  # ticks on the values the bars stand for
                st = 1.0 if b - a <= 16 else float(max(1, round(st)))
            if domain is None and not centered:  # widen to whole ticks at both ends
                a, b = math.floor(a / st + 1e-9) * st, math.ceil(b / st - 1e-9) * st
            xlo, xhi = a, b
            xt = SC.ticks(math.ceil(a / st - 1e-9) * st, b, st)
        xfmt = SC.tick_formatter(xt, unit, False, tick_format)
        vfmt = SC.formatter(fmt, decimals, yunit,
                            False, [h for hs in heights for h in hs])
        lift = values or (ng > 1 and not want_legend)  # labels may sit above the tallest bar
        PL = max((T.width(yfmt(t), th.TICK_SIZE) for t in ytk), default=10) + 14 + (18 if ylabel else 0)
        PR = max(12.0, T.width(xfmt(xt[-1]), th.TICK_SIZE) / 2 + 2) if xt else 12.0
        PT = 26 if lift else 12
        PB = 30 + (24 if xlabel else 0)
        PW, PH = W - PL - PR, H - PT - PB
        X = lambda v: PL + PW * ((v - xlo) / (xhi - xlo) if xhi > xlo else 0.5)
        Y = lambda v: PT + PH * (1 - (min(max(v, ylo), yhi) - ylo) / ((yhi - ylo) or 1))
        out = []
        for t in ytk:
            out.append(S.line(PL, Y(t), PL + PW, Y(t), th.AXIS if t == ylo else th.GRID))
            out.append(S.text(PL - 10, Y(t) + 4, yfmt(t), th.TICK_SIZE, th.MUTED, "end"))
        for t in xt:
            out.append(S.text(X(t), PT + PH + 20, xfmt(t), th.TICK_SIZE, th.MUTED, "middle"))
        if xlabel:
            out.append(S.text(PL + PW / 2, PT + PH + 46, xlabel, 12.5, th.INK2, "middle"))
        if ylabel:
            out.append(S.rotated(13, PT + PH / 2, ylabel, size=12))
        base = Y(max(ylo, 0))
        segs = []  # bar outlines, for placing labels
        if ng == 1:
            for k, h in enumerate(heights[0]):
                if h <= 0:
                    continue
                xa, xb = X(edges[k]), X(edges[k + 1])
                g = 1.0 if xb - xa >= 6 else 0.0
                out.append(S.rect(xa + g / 2, Y(h), xb - xa - g, base - Y(h), cols[0]))
                if values:
                    out.append(S.text((xa + xb) / 2, Y(h) - 5, vfmt(h), 12, th.INK2, "middle"))
        else:
            paths = []
            for hs, c in zip(heights, cols):
                nz = [k for k, h in enumerate(hs) if h > 0]
                if not nz:
                    paths.append(None)
                    continue
                a, b = nz[0], nz[-1]
                d = [f"M{S.n(X(edges[a]))},{S.n(base)}"]
                prev = (X(edges[a]), base)
                for k in range(a, b + 1):
                    yk = Y(hs[k])
                    d.append(f"V{S.n(yk)}H{S.n(X(edges[k + 1]))}")
                    segs.append((prev[0], prev[1], prev[0], yk))
                    segs.append((prev[0], yk, X(edges[k + 1]), yk))
                    prev = (X(edges[k + 1]), yk)
                d.append(f"V{S.n(base)}")
                segs.append((prev[0], prev[1], prev[0], base))
                paths.append("".join(d))
            for d, c in zip(paths, cols):
                if d:
                    out.append(S.path(d + "Z", c, extra='fill-opacity="0.22"'))
            for d, c in zip(paths, cols):
                if d:
                    out.append(S.path(d, "none", c, 1.8, extra='stroke-linejoin="miter"'))
        if ref is not None:
            out.append(S.line(X(ref), PT, X(ref), PT + PH, th.MUTED, 1, "4 4"))
            if ref_label:
                out.append(S.text(X(ref) + 6, PT + 12, ref_label, 12, th.MUTED, halo=th.BG))
        # ---- direct labels for overlaid groups: above a bin where the group stands out
        legend_items = list(zip(names, cols)) if named else None
        if ng > 1 and len(named) == ng and not want_legend:
            taken: list[tuple[float, float, float, float]] = []
            if ref is not None and ref_label:
                taken.append((X(ref) + 2, PT, X(ref) + 10 + T.width(ref_label, 12), PT + 16))
            spots = []
            for gi in range(ng):
                w = key_width(names[gi])
                order = sorted(range(len(edges) - 1), key=lambda k: (
                    -(heights[gi][k] - max(heights[o][k] for o in range(ng) if o != gi)), -heights[gi][k], k))
                cands = []
                for k in order:
                    hk = heights[gi][k]
                    if hk <= 0 or hk < max(heights[o][k] for o in range(ng)):
                        continue
                    cx = (X(edges[k]) + X(edges[k + 1])) / 2
                    x0, x1 = cx - w / 2, cx + w / 2
                    over = [max(hs[m] for hs in heights) for m in range(len(edges) - 1)
                            if X(edges[m + 1]) > x0 and X(edges[m]) < x1]
                    roof = Y(max(over + [hk]))
                    if roof < Y(hk) - 24:  # another group is much taller under the label: too far from this one
                        continue
                    y1 = roof - 6
                    cands.append((x0, y1 - LABEL_SIZE * 1.25, x1, y1))
                spot = free_spot(cands, segs, taken, (PL, 0, PL + PW, PT + PH))
                if spot is None:
                    spots = None
                    break
                taken.append(spot)
                spots.append(spot)
            if spots:
                for spot, nm, c in zip(spots, names, cols):
                    out.append(key_label(spot, nm, c, "square"))
                legend_items = None
        return Body("".join(out), H, legend_items, meta={"plot_x": (PL, PL + PW)})

    return Figure(render, title=title, subtitle=subtitle, legend=legend,
                  legend_position=legend_position, frame=frame, width=width, kind="histogram")
