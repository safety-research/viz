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


def scale_color(v: float, scale: str, lo: float, hi: float, center: float | None = None, low: str = "coral",
                high: str = "blue") -> tuple[str, float]:
    """The fill for value v and how far along its scale it sits (0 to 1). A sequential scale runs from lo to hi;
    "diverging" deepens toward `low` below center (0 by default) and toward `high` above it. Read at draw time, so
    the dark theme's scales apply. The heatmap's cells and the token figure's boxes both use it."""
    if scale == "diverging":
        c = 0.0 if center is None else center
        span = max(abs(hi - c), abs(lo - c)) or 1
        t = min(abs(v - c) / span, 1)
        end = th.SCALES.get(high, (None, th.color(high)))[1] if v >= c else th.SCALES.get(low, (None, th.color(low)))[1]
        return th.mix(th.SURFACE, end, t), t
    a, b = th.SCALES[scale] if scale in th.SCALES else (th.SURFACE, th.color(scale))
    t = 0.0 if hi == lo else min(max((v - lo) / (hi - lo), 0), 1)
    return th.mix(a, b, t), t


def heatmap(data, *, rows=None, cols=None, scale="coral", domain=None, center=None, unit=UNSET, decimals=None,
            fmt=None, signed=False, col_groups=None, sort=None, cell_width=None, cell_height=30, values=True,
            threshold=0.55, low="coral", high="blue", title=None, subtitle=None, frame=None,
            width=None) -> Figure:
    """Heatmap table.

    scale: "coral" (default, the accent's hue), "blue", "sage", "green", or "diverging" (`low` color below `center`, `high` above;
    coral below and blue above by default, so pass low="blue", high="coral" when higher is worse).
    col_groups: [("Keep it at a cost", ["At 10% lower score", "At 30% lower score"])] puts a muted heading
    with a rule over those columns. sort: a column name to sort rows by (descending), or a key function.
    Cell text is white or ink, whichever contrasts more with the cell (threshold is kept for old calls; unused).
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

    def fill_of(v):
        return scale_color(v, scale, lo, hi, center, low, high)

    def render(W: float) -> Body:
        G, CH = 6, cell_height
        L = max(T.width(r, 13.5) for r in rlabels) + 14 if rlabels else 60
        L = max(L, 0.2 * W)
        nc = len(clabels)
        CW = cell_width or min(158, (W - L - G * (nc - 1)) / nc)
        head_lines = [T.wrap(c, CW - 6, 13.5, "sans", 600) for c in clabels]
        nl = max(len(x) for x in head_lines)
        widest = max((T.width(ln, 13.5, "sans", 600) for x in head_lines for ln in x), default=0)
        slant = cell_width is None and widest > CW - 4  # a word wider than its column: write the headers on a slant
        top = 22 if col_groups else 0  # headers sit under the group headings
        hy = top + 18  # first header baseline
        Y0 = hy + (nl - 1) * 17 + 18
        if slant:
            cos, sin = math.cos(math.radians(50)), math.sin(math.radians(50))
            over = L + (nc - 1) * (CW + G) + CW / 2 + T.width(clabels[-1], 13.5, "sans", 600) * cos - W
            if over > 0:  # keep the last slanted header inside the figure
                CW = max(18.0, CW - over / (nc - 0.5))
            Y0 = top + max(T.width(c, 13.5, "sans", 600) for c in clabels) * sin + 16
        X0 = L
        out = []
        cx = lambda j: X0 + j * (CW + G)
        # values that don't fit their cells: the smallest text size first, then without the unit, else left out
        vsize, vfmt, show = 13.0, fmtv, values
        if values:
            texts = [fmtv(v) for r in vals for v in r if v is not None]
            fits = lambda f, size: max((T.width(f(v), size, "sans", 600) for r in vals for v in r if v is not None),
                                       default=0) <= CW - 4
            if not fits(fmtv, vsize):
                vsize = th.MIN_TEXT
                if not fits(fmtv, vsize):
                    bare = (lambda v: fmtv(v).removesuffix(unit)) if unit and all(t.endswith(unit) for t in texts) else fmtv
                    vfmt, show = (bare, True) if fits(bare, vsize) else (fmtv, False)
        if col_groups:
            for label, members in col_groups:
                idx = [clabels.index(m) for m in members]
                a, b = min(idx), max(idx)
                mid = (cx(a) + cx(b) + CW) / 2
                out.append(S.text(mid, 18, label, 12.5, th.MUTED, "middle"))
                out.append(S.line(cx(a), 24, cx(b) + CW, 24, th.GRID))
        for j, lines in enumerate(head_lines):
            if slant:
                x, y = cx(j) + CW / 2 - 3, Y0 - 8
                out.append(f'<text transform="translate({S.n(x)},{S.n(y)}) rotate(-50)" '
                           f'{S.font_attrs(13.5, "sans", 600, False, th.INK)}>{S.esc(clabels[j])}</text>')
                continue
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
                f, _ = fill_of(v)
                out.append(S.rect(cx(j), y, CW, CH, f, 5))
                if show:
                    out.append(S.text(cx(j) + CW / 2, y + CH / 2 + 4.5, vfmt(v), vsize, th.text_on(f),
                                      "middle", 600))
        H = Y0 + len(rlabels) * (CH + G) - G + 4
        return Body("".join(out), H)

    return Figure(render, title=title, subtitle=subtitle, legend=False, frame=frame, width=width,
                  kind="heatmap")
