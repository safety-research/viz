"""The matrix: viz's one chart for a grid of values (models against evals or attacks, a correlation matrix, measures
of several traits), drawn like the correlation matrices in Anthropic's posts. Cells touch, with thin white lines
between them; a color bar in one tone (orange by default) keys the colors; each value is written in its cell; rows
are labeled at the left and columns under the matrix."""
from __future__ import annotations

import hashlib
import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from .. import scale as SC
from .. import svg as S
from .. import text as T
from .. import theme as th
from ..data import _is_frame
from ..figure import Body, Figure
from .common import UNSET, resolve_unit

CELL_MAX = 112  # the widest a cell gets, so a small matrix doesn't stretch across the page
CELL_H, CELL_H_TWO = 36, 50  # a cell's height with one line, and with a second (an interval) under it
GAP, GROUP_GAP = 2, 6  # the white lines between cells, and the wider ones between groups of rows or columns
HATCH = 6  # px between the hatch lines of a cell whose interval includes zero
BAR_W, BAR_H = 168, 10  # the color bar


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
    """The fill for value v and how far along its scale it sits (0 to 1). A one-tone scale runs from a light tint of
    its hue at lo to its deep end at hi; "diverging" runs from a light neutral at center (0 by default) toward `low`
    below it and `high` above it. Read at draw time, so the dark theme's scales apply. Matrices and shaded tokens
    use it."""
    if scale == "diverging":
        c = 0.0 if center is None else center
        span = max(abs(hi - c), abs(lo - c)) or 1
        t = min(abs(v - c) / span, 1)
        return th.tone(high if v >= c else low, t), t
    t = 0.0 if hi == lo else min(max((v - lo) / (hi - lo), 0), 1)
    return th.tone(scale, th.SCALE_START + (1 - th.SCALE_START) * t), t


def scale_ends(scale: str, lo: float, hi: float, center: float | None = None) -> tuple[float, float]:
    """The values at the two ends of a scale's colors: a diverging scale reaches as far on both sides of its center."""
    if scale != "diverging":
        return lo, hi
    c = 0.0 if center is None else center
    span = max(abs(hi - c), abs(lo - c)) or 1
    return c - span, c + span


def color_bar(lo: float, hi: float, fill, label: str | None, fmt) -> tuple[str, float, float]:
    """The color bar of a matrix: its label over a smooth bar, the low value at its left and the high value at its
    right. Returns (svg, width, height)."""
    stops = "".join(f'<stop offset="{k * 10}%" stop-color="{fill(lo + (hi - lo) * k / 10)}"/>' for k in range(11))
    gid = "viz-bar-" + hashlib.sha1(stops.encode()).hexdigest()[:10]  # the same bar, the same id
    lo_s, hi_s = fmt(lo), fmt(hi)
    bx = T.width(lo_s, th.TICK_SIZE) + 8
    top = T.line_height(th.LEGEND_SIZE) + 4 if label else 0.0
    out = [f'<defs><linearGradient id="{gid}">{stops}</linearGradient></defs>',
           S.rect(bx, top, BAR_W, BAR_H, f"url(#{gid})", 2),
           S.text(bx - 8, top + BAR_H / 2 + 4, lo_s, th.TICK_SIZE, th.MUTED, "end"),
           S.text(bx + BAR_W + 8, top + BAR_H / 2 + 4, hi_s, th.TICK_SIZE, th.MUTED)]
    width = bx + BAR_W + 8 + T.width(hi_s, th.TICK_SIZE)
    if label:
        out.append(S.text(bx + BAR_W / 2, T.baseline(th.LEGEND_SIZE), label, th.LEGEND_SIZE, th.INK2, "middle"))
        width = max(width, bx + BAR_W / 2 + T.width(label, th.LEGEND_SIZE) / 2)
    return "".join(out), width, top + BAR_H


def hatch(x: float, y: float, w: float, h: float, ink: str) -> str:
    """Diagonal lines across a w-by-h cell: the mark for an interval that includes zero. Drawn as lines rather than
    an SVG pattern, so every renderer and PDF reader shows the same thing."""
    d, c = [], HATCH / 2
    while c < w + h:
        u1, u2 = max(0.0, c - h), min(w, c)
        d.append(f"M{S.n(x + u1)},{S.n(y + c - u1)} L{S.n(x + u2)},{S.n(y + c - u2)}")
        c += HATCH
    return S.path(" ".join(d), "none", ink, 1, extra='stroke-opacity="0.3"')


@dataclass
class Cell:
    """One drawn cell of a matrix."""
    fill: str
    text: str | None = None    # the value as written
    bare: str | None = None    # the same without its unit, for cells too narrow for it
    second: str | None = None  # a second line under the value, such as its interval
    boxed: bool = False        # outlined in ink, such as the validity diagonal of an MTMM matrix
    hatched: bool = False      # hatched, such as an interval that includes zero
    ink: str | None = None     # the text's color; None picks white or ink, whichever reads on the fill


def grid(W: float, rows: list[str], cols: list[str], cells: dict[tuple[int, int], Cell], bar, *,
         row_groups=None, col_groups=None, key=(), swatch: str | None = None, cell_w: float | None = None,
         cell_h: float | None = None) -> Body:
    """Draw a matrix at width W: the cells (keyed by (row, column) index; a cell left out stays blank), the color
    bar (svg, width, height) at the top right, and the key [("box" | "hatch" | "text", label)] at the top left.
    row_groups, col_groups: [(label, first, last)] index ranges set apart by a wider white line, labeled beside the
    rows with a rule or under the columns. Text that doesn't fit its cell is written smaller, then without its unit
    (Cell.bare), else left out; a second line that doesn't fit is left out (Body.meta["second_left_out"])."""
    gap_after = lambda groups, k: GROUP_GAP if any(k == last for _, _, last in groups or ()) else GAP
    offsets = lambda n, size, groups: [sum(size + gap_after(groups, i) for i in range(k)) for k in range(n)]
    gw = max((T.width(g, 12.5) for g, _, _ in row_groups or ()), default=0.0)
    X0 = (gw + 19 if row_groups else 0) + max((T.width(r, 13.5) for r in rows), default=0) + 12
    nc = len(cols)
    gaps = sum(gap_after(col_groups, i) for i in range(nc - 1))
    CW = cell_w or min(CELL_MAX, (W - X0 - gaps) / nc)
    heads = [T.wrap(c, CW - 6, 13) for c in cols]
    slant = cell_w is None and max((T.width(w, 13) for c in cols for w in str(c).split()), default=0) > CW - 4
    # the cells' text: the largest size that fits every cell, then the values without their unit, else none
    texts = [c.text for c in cells.values() if c.text]
    fits = lambda strs, size: max((T.width(s, size) for s in strs), default=0) <= CW - 6
    size, use_bare, show = 13.0, False, True
    if not fits(texts, size):
        size = th.MIN_TEXT
        if not fits(texts, size):
            bares = [c.bare or c.text for c in cells.values() if c.text]
            use_bare, show = (True, True) if fits(bares, size) else (False, False)
    seconds = [c.second for c in cells.values() if c.second]
    two = bool(seconds) and show and fits(seconds, th.MIN_TEXT) and CW >= 40
    CH = cell_h or (CELL_H_TWO if two else CELL_H)
    xo, yo = offsets(nc, CW, col_groups), offsets(len(rows), CH, row_groups)
    grid_w = xo[-1] + CW if nc else 0.0

    # the key at the top left, the color bar at the top right, over the matrix's right edge
    out, x, key_h = [], 0.0, 0.0
    sw_fill = swatch or th.mix(th.SURFACE, th.BG, 0.5)
    for kind, label in key:
        mark = ""
        if kind == "box":
            mark = S.rect(0, 1, 13, 13, sw_fill) + S.rect(0.75, 1.75, 11.5, 11.5, "none",
                                                          extra=f'stroke="{th.INK}" stroke-width="1.5"')
        elif kind == "hatch":
            mark = S.rect(0, 1, 13, 13, sw_fill) + hatch(0, 1, 13, 13, th.text_on(sw_fill))
        tx = 21 if mark else 0
        out.append(S.group(mark + S.text(tx, 12, label, th.LEGEND_SIZE, th.INK2), x, 0))
        x += tx + T.width(label, th.LEGEND_SIZE) + 22
        key_h = 15
    bar_svg, bar_w, bar_h = bar
    bx = max(X0 + grid_w - bar_w, 0.0)
    by = 0.0
    if x and bx < x:  # no room beside the key: the bar goes under it
        by = key_h + 10
    out.append(S.group(bar_svg, bx, by))
    Y0 = max(key_h, by + bar_h) + 18

    # rows: each group beside its rows with a rule, then the row labels
    for label, a, z in row_groups or ():
        y1, y2 = Y0 + yo[a], Y0 + yo[z] + CH
        out.append(S.text(gw, (y1 + y2) / 2 + 4.5, label, 12.5, th.MUTED, "end"))
        out.append(S.line(gw + 9, y1, gw + 9, y2, th.GRID))
    for i, r in enumerate(rows):
        out.append(S.text(X0 - 12, Y0 + yo[i] + CH / 2 + 4.5, r, 13.5, th.INK2, "end"))

    # the cells
    for (i, j), c in cells.items():
        x, y = X0 + xo[j], Y0 + yo[i]
        out.append(S.rect(x, y, CW, CH, c.fill))
        if c.hatched:
            out.append(hatch(x, y, CW, CH, th.text_on(c.fill)))
        text = (c.bare or c.text) if use_bare else c.text
        if show and text:
            ink, halo = c.ink or th.text_on(c.fill), c.fill if c.hatched else None  # clear of the hatching
            if two and c.second:
                out.append(S.text(x + CW / 2, y + CH / 2 - 2.5, text, size, ink, "middle", halo=halo))
                out.append(S.text(x + CW / 2, y + CH / 2 + 13, c.second, th.MIN_TEXT,
                                  c.ink or th.text_on(c.fill, soft=True), "middle", halo=halo))
            else:
                out.append(S.text(x + CW / 2, y + CH / 2 + 4.5, text, size, ink, "middle", halo=halo))
        if c.boxed:
            out.append(S.rect(x + 0.75, y + 0.75, CW - 1.5, CH - 1.5, "none",
                              extra=f'stroke="{th.INK}" stroke-width="1.5"'))

    # columns, under the matrix: the labels (on a slant when a word is wider than its column), then each group
    # under its columns with a rule over it
    yb = Y0 + (yo[-1] + CH if rows else 0)
    if slant:
        sin = math.sin(math.radians(50))
        for j, c in enumerate(cols):
            out.append(f'<text transform="translate({S.n(X0 + xo[j] + CW / 2 + 4)},{S.n(yb + 14)}) rotate(-50)" '
                       f'text-anchor="end" {S.font_attrs(13, "sans", 400, False, th.INK2)}>{S.esc(c)}</text>')
        yl = yb + 14 + max(T.width(c, 13) for c in cols) * sin + 8
    else:
        nl = max((len(h) for h in heads), default=1)
        for j, lines in enumerate(heads):
            for k, ln in enumerate(lines):
                out.append(S.text(X0 + xo[j] + CW / 2, yb + 18 + k * 16, ln, 13, th.INK2, "middle"))
        yl = yb + 18 + (nl - 1) * 16 + 10
    for label, a, z in col_groups or ():
        x1, x2 = X0 + xo[a], X0 + xo[z] + CW
        out.append(S.line(x1, yl, x2, yl, th.GRID))
        out.append(S.text((x1 + x2) / 2, yl + 17, label, 12.5, th.MUTED, "middle"))
    H = (yl + 22) if col_groups else yl
    return Body("".join(out), H, meta={"plot_x": (X0, X0 + grid_w), "second_left_out": bool(seconds) and not two})


def heatmap(data, *, rows=None, cols=None, scale="coral", domain=None, center=None, unit=UNSET, decimals=None,
            fmt=None, signed=False, values=True, label=None, row_groups=None, col_groups=None, sort=None,
            cell_width=None, cell_height=None, threshold=0.55, low="coral", high="blue", title=None, subtitle=None,
            width=None) -> Figure:
    """The matrix: a grid of values, such as models against evals or attacks, or a correlation matrix, drawn as in
    Anthropic's posts: cells that touch, each value written in its cell, a color bar, rows labeled at the left and
    columns under the matrix.

    scale: one tone: "coral" (the default, the accent's hue), "blue", "sage" or "green", from a light tint at the low
    end to the deep end; or "diverging" (`low` below `center` and `high` above, from a light neutral).
    domain: (low, high), the values at the ends of the colors; by default 0 to 100 for percents, else from 0 (or the
    lowest value, when one is below 0) to the highest value; pass (0, 1) for correlations. label: what the colors mean, written over the color bar.
    values: True writes every value; "lower" writes those on and below the diagonal only, as for a correlation
    matrix, while every cell keeps its color; False writes none.
    row_groups, col_groups: [("Group", [names])] set those rows or columns apart with a wider white line and label
    them beside the rows or under the columns. sort: a column name to sort rows by (descending), or a key function.
    A value too wide for its cell is written smaller, then without its unit, else left out (the colors stay).
    cell_width, cell_height: fixed cell sizes in px. threshold is kept for old calls and unused.
    """
    rlabels, clabels, vals = _matrix(data, rows, cols)
    unit, _ = resolve_unit(unit)
    if values not in (True, False, "lower"):
        raise ValueError(f"values={values!r}: use True, False or 'lower'")
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
    else:  # counts and rates start at zero, as bars do
        lo, hi = (min(0.0, min(flat)) if scale != "diverging" else min(flat), max(flat)) if flat else (0.0, 1.0)
    fmtv = SC.formatter(fmt, decimals, unit, signed, flat)
    fill_of = lambda v: scale_color(v, scale, lo, hi, center, low, high)[0]

    def groups(spec, names, what):
        out = []
        for g, members in spec or ():
            idx = [names.index(str(m)) if str(m) in names else None for m in members]
            if None in idx:
                raise ValueError(f"{what}_groups: {members[idx.index(None)]!r} is not one of the {what}s")
            out.append((str(g), min(idx), max(idx)))
        return out

    def render(W: float) -> Body:
        cells = {}
        for i, row in enumerate(vals):
            for j, v in enumerate(row):
                if v is None:
                    cells[(i, j)] = Cell(th.mix(th.SURFACE, th.BG, 0.5), "–", ink=th.MUTED)
                    continue
                written = values is True or (values == "lower" and j <= i)
                text = fmtv(v) if written else None
                bare = text.removesuffix(unit) if text and unit else text
                cells[(i, j)] = Cell(fill_of(v), text, bare)
        e0, e1 = scale_ends(scale, lo, hi, center)
        bar = color_bar(e0, e1, fill_of, label, SC.tick_formatter([e0, e1], unit, signed))
        return grid(W, rlabels, clabels, cells, bar, row_groups=groups(row_groups, rlabels, "row"),
                    col_groups=groups(col_groups, clabels, "col"), cell_w=cell_width, cell_h=cell_height)

    return Figure(render, title=title, subtitle=subtitle, legend=False, width=width, kind="heatmap")
