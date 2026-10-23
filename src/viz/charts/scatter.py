"""Scatter with direct point labels, an optional y = x line or fitted trend, and muted annotations."""
from __future__ import annotations

import math
from collections.abc import Mapping

from .. import scale as SC
from .. import svg as S
from .. import text as T
from .. import theme as th
from ..figure import Body, Figure
from .common import plot_height


def _points(points):
    if hasattr(points, "itertuples") and hasattr(points, "columns"):  # DataFrame: index = label, first two columns
        return [(str(i), float(a), float(b)) for i, a, b, *_ in points.itertuples()]
    if isinstance(points, Mapping):
        return [(str(k), float(v[0]), float(v[1])) for k, v in points.items()]
    out = []
    for i, p in enumerate(points):
        if len(p) == 3:
            out.append((str(p[0]), float(p[1]), float(p[2])))
        else:
            out.append((f"#{i}", float(p[0]), float(p[1])))
    return out


def scatter(points, *, labels=None, label_offsets=None, color="blue", colors=None, size=6.5,
            xdomain=None, ydomain=None, xticks=None, yticks=None, xunit="", yunit="", xlabel=None, ylabel=None,
            diagonal=False, trend=None, trend_label=None, annotations=None, height=None,
            title=None, subtitle=None, legend=None, frame=None, width=None) -> Figure:
    """Scatter plot.

    points: {label: (x, y)}, [(label, x, y)], [(x, y)] or a DataFrame (index = labels).
    labels: True for all, or a list of the labels to write next to their points.
    label_offsets: {label: (dx, dy, "start"|"end")} to place a label by hand.
    diagonal: True or a label string draws y = x. trend: "fit" (least squares) or (slope, intercept).
    annotations: [(x, y, "text")] in data coordinates, muted. colors: {label: color} per point.
    """
    pts = _points(points)
    show = {p[0] for p in pts} if labels is True else set(labels or [])

    def render(W: float) -> Body:
        H = height or plot_height(1.5)  # relationships read best close to square
        PL = 64 + (16 if ylabel else 0)
        PT, PR = 14, 18
        PB = 34 + (24 if xlabel else 0)
        PW, PH = W - PL - PR, H - PT - PB
        xs, ys = [p[1] for p in pts], [p[2] for p in pts]
        if xticks is not None:
            xlo, xhi, xt = min(xticks), max(xticks), list(xticks)
        else:
            xlo, xhi, xt = SC.domain(xs, *(xdomain or (None, None)), percent=xunit == "%")
        if yticks is not None:
            ylo, yhi, yt = min(yticks), max(yticks), list(yticks)
        else:
            ylo, yhi, yt = SC.domain(ys, *(ydomain or (None, None)), percent=yunit == "%")
        X = lambda v: PL + PW * (v - xlo) / (xhi - xlo)
        Y = lambda v: PT + PH * (1 - (v - ylo) / (yhi - ylo))
        fx, fy = SC.tick_formatter(xt, xunit), SC.tick_formatter(yt, yunit)
        out = []
        for t in xt:
            out.append(S.line(X(t), PT, X(t), PT + PH, th.GRID))
            out.append(S.text(X(t), PT + PH + 20, fx(t), th.TICK_SIZE, th.MUTED, "middle"))
        for t in yt:
            out.append(S.line(PL, Y(t), PL + PW, Y(t), th.GRID))
            out.append(S.text(PL - 10, Y(t) + 4, fy(t), th.TICK_SIZE, th.MUTED, "end"))
        if xlabel:
            out.append(S.text(PL + PW / 2, PT + PH + 46, xlabel, 13, th.INK2, "middle"))
        if ylabel:
            out.append(S.rotated(14, PT + PH / 2, ylabel, size=13))
        ref_lines = []
        if diagonal:
            a, b = max(xlo, ylo), min(xhi, yhi)
            ref_lines.append(((a, a), (b, b), diagonal if isinstance(diagonal, str) else None, "diagonal"))
        if trend is not None:
            if trend == "fit":
                mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
                sxx = sum((x - mx) ** 2 for x in xs) or 1
                slope = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx
                icpt = my - slope * mx
            else:
                slope, icpt = trend
            x_a, x_b = xlo, xhi
            # clip to the plot box
            pts_ = []
            for xv in (x_a, x_b):
                yv = slope * xv + icpt
                pts_.append((xv, min(max(yv, ylo), yhi)))
            ref_lines.append((pts_[0], pts_[1], trend_label, "trend"))
        for (x1, y1), (x2, y2), lab, kind in ref_lines:
            if kind == "diagonal":
                out.append(S.line(X(x1), Y(y1), X(x2), Y(y2), th.MUTED, 1.5))
            else:
                out.append(S.line(X(x1), Y(y1), X(x2), Y(y2), th.AXIS, 1.4, "4 4"))
            if lab:
                ang = -math.degrees(math.atan2(Y(y1) - Y(y2), X(x2) - X(x1)))
                tx, ty = X(x1 + 0.84 * (x2 - x1)), Y(y1 + 0.84 * (y2 - y1))
                out.append(f'<text transform="translate({S.n(tx)},{S.n(ty + 18)}) rotate({S.n(ang)})" '
                           f'{S.font_attrs(12, "sans", 400, False, th.MUTED)} text-anchor="middle">{S.esc(lab)}</text>')
        for a in annotations or []:
            ax, ay, txt = a[0], a[1], a[2]
            for k, ln in enumerate(str(txt).split("\n")):
                out.append(S.text(X(ax), Y(ay) + k * 17, ln, 12.5, th.MUTED))
        for lab, x, y in pts:
            fill = th.color((colors or {}).get(lab, color)) if isinstance(colors, Mapping) else th.color(color)
            out.append(S.circle(X(x), Y(y), size, fill, th.BG, 2))
        # labels: hand offsets first, then the first free spot among right / left / above / below
        placed: list[tuple[float, float, float, float]] = [(X(x) - size, Y(y) - size, X(x) + size, Y(y) + size) for _, x, y in pts]
        offs = label_offsets or {}
        for lab, x, y in pts:
            if lab not in show:
                continue
            w = T.width(lab, 12)
            px, py = X(x), Y(y)
            if lab in offs:
                dx, dy, anc = (list(offs[lab]) + ["start"])[:3]
                cands = [(dx, dy, anc)]
            else:
                cands = [(size + 4, 4, "start"), (-size - 4, 4, "end"), (0, -size - 6, "middle"), (0, size + 15, "middle")]
            best = None
            for dx, dy, anc in cands:
                x0 = px + dx - (w if anc == "end" else w / 2 if anc == "middle" else 0)
                box = (x0, py + dy - 11, x0 + w, py + dy + 3)
                inside = box[0] >= 0 and box[2] <= W
                hit = any(not (box[2] < b[0] or box[0] > b[2] or box[3] < b[1] or box[1] > b[3]) for b in placed)
                if inside and not hit:
                    best = (dx, dy, anc, box)
                    break
                if best is None and inside:
                    best = (dx, dy, anc, box)
            if best is None:
                dx, dy, anc = cands[0]
                best = (dx, dy, anc, (px, py, px, py))
            dx, dy, anc, box = best
            placed.append(box)
            out.append(S.text(px + dx, py + dy, lab, 12, th.INK2, anc, halo=th.BG))
        return Body("".join(out), H)

    return Figure(render, title=title, subtitle=subtitle, legend=legend, frame=frame, width=width,
                  kind="scatter")
