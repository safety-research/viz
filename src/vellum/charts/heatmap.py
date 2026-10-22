"""Heatmap table: rounded cells in one hue (more is darker), the number written in each cell."""
from __future__ import annotations

import math
from collections.abc import Mapping, Sequence

from .. import scale as SC
from .. import svg as S
from .. import text as T
from .. import theme as th
from ..data import _is_frame
from ..figure import Body, Figure
from .common import UNSET, resolve_unit


def _matrix(data, rows, cols):
    if _is_frame(data):
        cols = cols or [str(c) for c in data.columns]
        rows = rows or [str(i) for i in data.index]
        vals = [[None if v is None or math.isnan(float(v)) else float(v) for v in r] for r in data.itertuples(index=False)]
        return rows, cols, vals
    if isinstance(data, Mapping):
        rows = rows or [str(k) for k in data]
        first = next(iter(data.values()))
        if isinstance(first, Mapping):
            cols = cols or list(dict.fromkeys(str(c) for v in data.values() for c in v))
            vals = [[(None if data[r].get(c) is None else float(data[r][c])) for c in cols] for r in data]
        else:
            if cols is None:
                raise ValueError("pass cols=[...] when rows map to lists")
            vals = [[None if v is None else float(v) for v in data[r]] for r in data]
        return [str(r) for r in rows], list(cols), vals
    if isinstance(data, Sequence):
        if rows is None or cols is None:
            raise ValueError("a 2-D list needs rows=[...] and cols=[...]")
        return list(rows), list(cols), [[None if v is None else float(v) for v in r] for r in data]
    raise TypeError("heatmap data: {row: {col: value}}, {row: [values]} with cols=, a 2-D list, or a DataFrame")


def heatmap(data, *, rows=None, cols=None, scale="blue", domain=None, center=None, unit=UNSET, decimals=None,
            fmt=None, signed=False, col_groups=None, sort=None, cell_width=None, cell_height=30, values=True,
            threshold=0.55, low="coral", high="blue", title=None, subtitle=None, frame=None,
            width=None) -> Figure:
    """Heatmap table.

    scale: "blue" (default), "coral", "sage", "green", or "diverging" (`low` color below `center`, `high` above;
    coral below and blue above by default, so pass low="blue", high="coral" when higher is worse).
    col_groups: [("Keep it at a cost", ["At 10% lower score", "At 30% lower score"])] puts a muted heading
    with a rule over those columns. sort: a column name to sort rows by (descending), or a key function.
    """
    rlabels, clabels, vals = _matrix(data, rows, cols)
    unit, _ = resolve_unit(unit)
    if sort is not None:
        if callable(sort):
            order = sorted(range(len(rlabels)), key=lambda i: sort(rlabels[i], vals[i]))
        else:
            j = clabels.index(sort)
            order = sorted(range(len(rlabels)), key=lambda i: -(vals[i][j] if vals[i][j] is not None else -1e18))
        rlabels = [rlabels[i] for i in order]
        vals = [vals[i] for i in order]
    flat = [v for r in vals for v in r if v is not None]
    if domain is not None:
        lo, hi = domain
    elif unit == "%" and flat and min(flat) >= 0 and max(flat) <= 100:
        lo, hi = 0.0, 100.0
    else:
        lo, hi = (min(flat), max(flat)) if flat else (0.0, 1.0)
    fmtv = SC.formatter(fmt, decimals, unit, signed, flat)
    if decimals is None and fmt is None and unit == "%":
        fmtv = SC.formatter(None, 0, unit, signed)

    def fill_of(v):
        if scale == "diverging":
            c = 0.0 if center is None else center
            span = max(abs(hi - c), abs(lo - c)) or 1
            t = min(abs(v - c) / span, 1)
            end = th.SCALES.get(high, (None, th.color(high)))[1] if v >= c else th.SCALES.get(low, (None, th.color(low)))[1]
            return th.mix(th.SURFACE, end, t), t
        a, b = th.SCALES[scale] if scale in th.SCALES else (th.SURFACE, th.color(scale))
        t = 0.0 if hi == lo else min(max((v - lo) / (hi - lo), 0), 1)
        return th.mix(a, b, t), t

    def render(W: float) -> Body:
        G, CH = 6, cell_height
        L = max(T.width(r, 13.5) for r in rlabels) + 14 if rlabels else 60
        L = max(L, 0.2 * W)
        nc = len(clabels)
        CW = cell_width or min(158, (W - L - G * (nc - 1)) / nc)
        head_lines = [T.wrap(c, CW - 6, 13.5, "sans", 600) for c in clabels]
        nl = max(len(x) for x in head_lines)
        top = 22 if col_groups else 0  # headers sit under the group headings
        hy = top + 18  # first header baseline
        Y0 = hy + (nl - 1) * 17 + 18
        X0 = L
        out = []
        cx = lambda j: X0 + j * (CW + G)
        if col_groups:
            for label, members in col_groups:
                idx = [clabels.index(m) for m in members]
                a, b = min(idx), max(idx)
                mid = (cx(a) + cx(b) + CW) / 2
                out.append(S.text(mid, 18, label, 12.5, th.MUTED, "middle"))
                out.append(S.line(cx(a), 24, cx(b) + CW, 24, th.GRID))
        for j, lines in enumerate(head_lines):
            off = (nl - len(lines)) * 17
            for k, ln in enumerate(lines):
                out.append(S.text(cx(j) + CW / 2, hy + off + k * 17, ln, 13.5, th.INK, "middle", 600))
        for i, r in enumerate(rlabels):
            y = Y0 + i * (CH + G)
            out.append(S.text(X0 - 14, y + CH / 2 + 4.5, r, 13.5, th.INK2, "end"))
            for j, v in enumerate(vals[i]):
                if v is None:
                    out.append(S.rect(cx(j), y, CW, CH, th.mix(th.SURFACE, th.BG, 0.5), 5))
                    out.append(S.text(cx(j) + CW / 2, y + CH / 2 + 4.5, "–", 13, th.MUTED, "middle"))
                    continue
                f, t = fill_of(v)
                out.append(S.rect(cx(j), y, CW, CH, f, 5))
                if values:
                    out.append(S.text(cx(j) + CW / 2, y + CH / 2 + 4.5, fmtv(v), 13, "#FFFFFF" if t >= threshold else th.INK,
                                      "middle", 600))
        H = Y0 + len(rlabels) * (CH + G) - G + 4
        return Body("".join(out), H)

    return Figure(render, title=title, subtitle=subtitle, legend=False, frame=frame, width=width,
                  kind="heatmap")
