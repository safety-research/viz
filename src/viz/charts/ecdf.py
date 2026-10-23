"""Empirical cumulative distributions: one step line per group, the share of items at or below each value.

The y axis runs from 0 to 100%. Each line starts at its lowest value and, once it reaches 100%, runs on to the edge
of the plot. Lines are labeled directly beside the curve where it has room (the leftmost curve on its left, the
rightmost on its right), or with a legend when no spot is free. A reference line marks a threshold and writes the
share of each group at or below it.
"""
from __future__ import annotations

from collections.abc import Mapping
from itertools import pairwise

from .. import scale as SC
from .. import svg as S
from .. import text as T
from .. import theme as th
from ..figure import Body, Figure
from .common import as_set, row_colors, series_colors
from .dist import LABEL_SIZE, free_spot, key_label, key_width, quantile, samples


def _steps(vals: list[float], complementary: bool) -> list[tuple[float, float]]:
    """Corner points (value, percent) of the step line through sorted values."""
    s = sorted(vals)
    n = len(s)
    pts: list[tuple[float, float]] = []
    below = 0.0
    k = 0
    while k < n:
        u = s[k]
        while k < n and s[k] == u:
            k += 1
        f = 100 * k / n
        before, after = (100 - below, 100 - f) if complementary else (below, f)
        pts += [(u, before), (u, after)]
        below = f
    return pts


def ecdf(data, *, color=None, colors=None, highlight=None, accent="intervention", domain=None, ticks=None, step=None,
         unit="", tick_format=None, decimals=None, fmt=None, complementary=False, ref=None, ref_label=None,
         values=True, xlabel=None, ylabel=None, height=None,
         title=None, subtitle=None, legend=None, legend_position=None, frame=None, width=None) -> Figure:
    """ECDF: for each group, the share of items at or below each value, as a step line from 0 to 100%.

    data: a list of numbers, {name: [numbers]} for several groups, a pandas Series, or a DataFrame (one group per
          column). None and NaN are skipped.
    complementary=True draws the share above each value instead (a survival curve).
    The x values are plain numbers by default (unit=""; unit="%" for rates); domain, ticks, step and tick_format set
    the x axis. ref: a dashed vertical line at a threshold, ref_label its label; with values=True each curve's share
    at the threshold is written beside it, formatted by decimals or fmt. highlight: name(s) keep their color, the
    others go gray. Curves are labeled directly; legend=True uses a legend instead.
    """
    unit = "" if unit is None else str(unit)
    labels, vals, ns, _ = samples(data, flat_label="")
    if ns != 1:
        raise ValueError("ecdf data: a list of numbers or {name: [numbers]}, one list per group")
    groups = [g[0] for g in vals]
    names = labels
    ng = len(groups)
    hl = as_set(highlight)
    if hl:
        cols = row_colors(names, color=color, colors=colors, highlight=highlight, accent=accent)
    else:
        cols = series_colors(ng, colors if colors is not None else color, names)
    pooled = [v for g in groups for v in g]
    curves = [_steps(g, complementary) if g else [] for g in groups]
    want_legend = legend is True or isinstance(legend, (Mapping, list, tuple))

    def share(g: list[float], x: float) -> float:
        k = sum(1 for v in g if v <= x)
        return 100 * (len(g) - k if complementary else k) / len(g)

    def render(W: float) -> Body:
        H = height or 340
        ext = pooled + ([ref] if ref is not None else [])
        if ticks is not None:
            xlo, xhi, xt = min(ticks), max(ticks), list(ticks)
        elif domain is not None:
            xlo, xhi, xt = SC.domain(ext, domain[0], domain[1], unit == "%", step=step)
        else:
            xlo, xhi, xt = SC.domain(ext, percent=unit == "%", zero=False, step=step)
        xfmt = SC.tick_formatter(xt, unit, False, tick_format)
        ytk = [0, 25, 50, 75, 100]
        yfmt = SC.tick_formatter(ytk, "%")
        vfmt = SC.formatter(fmt, decimals, "%")
        PL = max(T.width(yfmt(t), th.TICK_SIZE) for t in ytk) + 14 + (18 if ylabel else 0)
        PR = max(12.0, T.width(xfmt(xt[-1]), th.TICK_SIZE) / 2 + 2)
        PT, PB = 12, 30 + (24 if xlabel else 0)
        PW, PH = W - PL - PR, H - PT - PB
        X = lambda v: PL + PW * ((min(max(v, xlo), xhi) - xlo) / (xhi - xlo) if xhi > xlo else 0.5)
        Y = lambda v: PT + PH * (1 - v / 100)
        out = []
        for t in ytk:
            out.append(S.line(PL, Y(t), PL + PW, Y(t), th.AXIS if t == 0 else th.GRID))
            out.append(S.text(PL - 10, Y(t) + 4, yfmt(t), th.TICK_SIZE, th.MUTED, "end"))
        for t in xt:
            out.append(S.text(X(t), PT + PH + 20, xfmt(t), th.TICK_SIZE, th.MUTED, "middle"))
        if xlabel:
            out.append(S.text(PL + PW / 2, PT + PH + 46, xlabel, 12.5, th.INK2, "middle"))
        if ylabel:
            out.append(S.rotated(13, PT + PH / 2, ylabel, size=12))
        segs: list[tuple[float, float, float, float]] = []
        taken: list[tuple[float, float, float, float]] = []
        ref_side = None  # the side of the reference line its label takes
        if ref is not None:
            out.append(S.line(X(ref), PT, X(ref), PT + PH, th.MUTED, 1, "4 4"))
            segs.append((X(ref), PT, X(ref), PT + PH))
            if ref_label:
                w = T.width(ref_label, 12)
                ref_side = "left" if X(ref) + 6 + w > PL + PW else "right"
                left = ref_side == "left"
                out.append(S.text(X(ref) + (-6 if left else 6), PT + 18, ref_label, 12, th.MUTED,
                                  "end" if left else "start", halo=th.BG))
                taken.append((X(ref) - 8 - w, PT + 6, X(ref), PT + 22) if left
                             else (X(ref), PT + 6, X(ref) + 8 + w, PT + 22))
        muted = [i for i in range(ng) if hl and names[i] not in hl]
        order = muted + [i for i in range(ng) if i not in muted]  # highlighted curves on top
        paths = {}
        lines = [[] for _ in range(ng)]
        for i in range(ng):
            if not curves[i]:
                continue
            # once at 100%, the line runs on to the edge of the plot
            lines[i] = [(xlo, 100.0)] + curves[i] if complementary else curves[i] + [(xhi, 100.0)]
            xy = [(X(a), Y(b)) for a, b in lines[i]]
            paths[i] = "M" + " L".join(f"{S.n(a)},{S.n(b)}" for a, b in xy)
            segs += [(a[0], a[1], b[0], b[1]) for a, b in pairwise(xy)]
        for i in order:
            if i in paths:
                sw = 1.6 if i in muted else 2.25
                out.append(S.path(paths[i], "none", cols[i], sw, extra='stroke-linejoin="round"'))
        # ---- each curve's share at the reference line
        if ref is not None and values:
            marks = sorted(((Y(share(groups[i], ref)), i) for i in range(ng) if groups[i]), key=lambda m: m[0])
            widest = max((T.width(vfmt(share(groups[i], ref)), 12) for _, i in marks), default=0)
            left = X(ref) + 9 + widest > PL + PW
            floor = PT + 22 + 8 if ref_side == ("left" if left else "right") else PT  # below the line's label
            ys = [max(m[0], floor) for m in marks]
            for k in range(1, len(ys)):  # push the value labels apart
                ys[k] = max(ys[k], ys[k - 1] + 15)
            over = (ys[-1] - (PT + PH - 2)) if ys else 0
            if over > 0:
                ys = [y - over for y in ys]
            for (yy, i), ly in zip(marks, ys):
                out.append(S.circle(X(ref), yy, 4, cols[i], th.BG, 1.5))
                s = vfmt(share(groups[i], ref))
                w = T.width(s, 12)
                lx = X(ref) - 9 if left else X(ref) + 9
                out.append(S.text(lx, ly + 4.3, s, 12, th.INK2, "end" if left else "start", halo=th.BG))
                taken.append((lx - w, ly - 8, lx, ly + 8) if left else (lx, ly - 8, lx + w, ly + 8))
        # ---- direct labels: beside each curve where it has room
        shown = [i for i in range(ng) if names[i] and groups[i]]
        legend_items = [(names[i], cols[i]) for i in shown] or None
        if shown and not want_legend and len(shown) == len([i for i in range(ng) if groups[i]]):
            rank = sorted(shown, key=lambda i: (quantile(sorted(groups[i]), 0.5), i))
            lh = LABEL_SIZE * 1.25
            spots = {}
            heights = [k / 50 for k in range(1, 50)]

            def near(f0: float) -> list[float]:  # heights in order of distance from f0
                return sorted(heights, key=lambda f: (abs(f - f0), f))
            for pos, i in enumerate(rank):
                if len(rank) == 1:
                    plan = [("right", f) for f in near(0.35)] + [("left", f) for f in near(0.65)]
                elif pos == 0:  # the leftmost curve: the empty space above and left of it
                    plan = [("left", f) for f in near(0.75)] + [("right", f) for f in near(0.4)]
                elif pos == len(rank) - 1:  # the rightmost: below and right of it
                    plan = [("right", f) for f in near(0.25)] + [("left", f) for f in near(0.6)]
                else:
                    plan = [(side, f) for f in near(0.5) for side in ("right", "left")]
                w = key_width(names[i])
                xy = [(X(a), Y(b)) for a, b in lines[i]]
                own = [(a[0], a[1], b[0], b[1]) for a, b in pairwise(xy)]
                cands = []
                for side, f in plan:
                    yc = Y(100 * (1 - f if complementary else f))
                    y0, y1 = yc - lh / 2 - 3, yc + lh / 2 + 3
                    xs = [x for (ax, ay, bx, by) in own if max(ay, by) >= y0 and min(ay, by) <= y1 for x in (ax, bx)]
                    if not xs:
                        continue
                    if side == "left":
                        cands.append((min(xs) - 8 - w, yc - lh / 2, min(xs) - 8, yc + lh / 2))
                    else:
                        cands.append((max(xs) + 8, yc - lh / 2, max(xs) + 8 + w, yc + lh / 2))
                spot = free_spot(cands, segs, taken + list(spots.values()), (PL + 4, PT, PL + PW, PT + PH))
                if spot is None:
                    spots = None
                    break
                spots[i] = spot
            if spots:
                for i in shown:
                    out.append(key_label(spots[i], names[i], cols[i], "line"))
                legend_items = None
        return Body("".join(out), H, legend_items, "line", meta={"plot_x": (PL, PL + PW)})

    return Figure(render, title=title, subtitle=subtitle, legend=legend,
                  legend_position=legend_position, frame=frame, width=width, kind="ecdf")
