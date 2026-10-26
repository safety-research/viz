"""Multitrait-multimethod matrix (Campbell and Fiske, 1959): the correlations among several traits, each measured by
two or more methods, drawn as a traditional heatmap: cells that touch, a color bar, the values written in the cells,
rows labeled at the left and columns under the matrix, with the validity diagonal (same trait, different methods)
boxed."""
from __future__ import annotations

import math
import warnings
from collections.abc import Mapping

from .. import scale as SC
from .. import svg as S
from .. import text as T
from .. import theme as th
from ..data import _is_frame
from ..figure import Body, Figure
from .cards import _colorbar
from .heatmap import scale_color

CELL_MAX = 84  # the widest a cell gets, so a small matrix doesn't fill the page
CELL_H, CELL_H_TWO = 38, 52  # a cell's height with its value, and with its value over its interval
GAP, BLOCK_GAP = 2, 6  # the white lines between cells, and the wider ones between method blocks
HATCH = 6  # px between hatch lines


def _num(v) -> float | None:
    if v is None:
        return None
    f = float(v)
    return None if math.isnan(f) else f


def _square(m, n: int, what: str, shape: str) -> list[list[float | None]]:
    """An n-by-n matrix of numbers (None for missing) from a 2-D list, a numpy array or a DataFrame."""
    rows = [list(r) for r in (m.itertuples(index=False) if _is_frame(m) else m)]
    if len(rows) != n or any(len(r) != n for r in rows):
        raise ValueError(f"{what} must be {n} by {n}: {shape}")
    return [[_num(v) for v in r] for r in rows]


def _intervals(ci, n: int, shape: str) -> list[list[tuple[float, float] | None]] | None:
    """Each correlation's interval, from (low matrix, high matrix) or from a matrix of (low, high) pairs."""
    if ci is None:
        return None
    if len(ci) == 2:  # an MTMM matrix has at least four rows, so two can only be the low and high bounds
        lo, hi = _square(ci[0], n, "ci's low bounds", shape), _square(ci[1], n, "ci's high bounds", shape)
        return [[None if lo[i][j] is None or hi[i][j] is None else (lo[i][j], hi[i][j]) for j in range(n)]
                for i in range(n)]
    rows = [list(r) for r in ci]
    if len(rows) != n or any(len(r) != n for r in rows):
        raise ValueError(f"ci must be (low, high) matrices or {n} by {n} (low, high) pairs: {shape}")
    pair = lambda p: None if p is None or _num(p[0]) is None or _num(p[1]) is None else (_num(p[0]), _num(p[1]))
    return [[pair(p) for p in r] for r in rows]


def _reliabilities(rel, traits: list[str], methods: list[str]) -> list[float | None] | None:
    """One reliability per row: a list in the matrix's order, {(method, trait): value} or {method: {trait: value}}."""
    if rel is None:
        return None
    if isinstance(rel, Mapping):
        nested = all(isinstance(v, Mapping) for v in rel.values())
        get = (lambda m, t: rel.get(m, {}).get(t)) if nested else (lambda m, t: rel.get((m, t)))
        return [_num(get(m, t)) for m in methods for t in traits]
    vals = [_num(v) for v in rel]
    if len(vals) != len(traits) * len(methods):
        raise ValueError(f"reliabilities needs one value per row ({len(traits) * len(methods)}), in the matrix's order")
    return vals


def _hatch(x: float, y: float, w: float, h: float, ink: str) -> str:
    """Diagonal lines across a w-by-h cell: the mark for an interval that includes zero. Drawn as lines rather than
    an SVG pattern, so every renderer and PDF reader shows the same thing."""
    a, bx, by = 0.0, w, h
    d = []
    c = 2 * a + HATCH / 2
    while c < bx + by:
        u1, u2 = max(a, c - by), min(bx, c - a)
        d.append(f"M{S.n(x + u1)},{S.n(y + c - u1)} L{S.n(x + u2)},{S.n(y + c - u2)}")
        c += HATCH
    return S.path(" ".join(d), "none", ink, 1, extra='stroke-opacity="0.3"')


def _key(items: list[tuple[str, float, float]], W: float) -> tuple[str, float]:
    """Key items, each (svg at its own origin, width, height), left to right, wrapping at the width W."""
    out, x, y, row_h = [], 0.0, 0.0, 0.0
    for svg_, w, h in items:
        if x and x + w > W:
            x, y, row_h = 0.0, y + row_h + 8, 0.0
        out.append(S.group(svg_, x, y))
        x, row_h = x + w + 22, max(row_h, h)
    return "".join(out), y + row_h


def mtmm(data, *, traits, methods, ci=None, reliabilities=None, triangle="lower", values=True, intervals=False,
         decimals=None, fmt=None, low="coral", high="blue", title=None, subtitle=None, width=None) -> Figure:
    """Multitrait-multimethod matrix: the correlations among several traits, each measured by two or more methods,
    the standard figure for convergent and discriminant validity (Campbell and Fiske, 1959).

    data: the square correlation matrix in method blocks: every trait under the first method, then every trait under
    the second, and so on, with the traits in the same order in each block; a 2-D list, a numpy array or a DataFrame.
    traits, methods: their names, in that order. The diagonal is left blank, or shows reliabilities= in parentheses:
    a list in the matrix's order, {(method, trait): value} or {method: {trait: value}}.
    ci: each correlation's interval, as (low, high) matrices or a matrix of (low, high) pairs. A cell whose interval
    includes zero is hatched, and intervals=True writes each interval under its value when it fits the cell.
    triangle: "lower" (the default) draws each pair once, below the diagonal; "full" draws the whole matrix.
    values: write each correlation in its cell; without them (or when they don't fit) a color bar is the key.
    Cells shade from orange at −1 through a light neutral at 0 to blue at +1 (low=, high= change the colors), as
    the color bar shows. A wider white line sets each method's block apart, and the validity diagonal is boxed.
    """
    traits, methods = [str(t) for t in traits], [str(m) for m in methods]
    nt, nm = len(traits), len(methods)
    if nt < 2 or nm < 2:
        raise ValueError("an MTMM matrix needs two or more traits and two or more methods")
    if triangle not in ("lower", "full"):
        raise ValueError(f"triangle={triangle!r}: use 'lower' or 'full'")
    n = nt * nm
    shape = f"one row and one column per trait under each method, method by method ({nm} methods x {nt} traits)"
    r = _square(data, n, "data", shape)
    cis = _intervals(ci, n, shape)
    rel = _reliabilities(reliabilities, traits, methods)
    if intervals and cis is None:
        raise ValueError("intervals=True writes each correlation's interval: pass ci= too")
    drawn = [(i, j) for i in range(n) for j in range(n) if i != j and (triangle == "full" or i > j)]
    fmtv = SC.formatter(fmt, decimals, "", False, [r[i][j] for i, j in drawn])
    zero = {(i, j) for i, j in drawn if cis and cis[i][j] and cis[i][j][0] <= 0 <= cis[i][j][1]}
    fill_of = lambda v: scale_color(v, "diverging", -1.0, 1.0, 0.0, low, high)[0]

    def render(W: float) -> Body:
        trim = triangle == "lower" and not rel  # nothing on the diagonal: the first row and the last column are empty
        rows, cols = list(range(1 if trim else 0, n)), list(range(n - 1 if trim else n))
        gaps = lambda idx: [BLOCK_GAP if a // nt != b // nt else GAP for a, b in zip(idx, idx[1:])]
        mw = max(T.width(m, 12.5) for m in methods)
        X0 = mw + 19 + max(T.width(t, 13.5) for t in traits) + 12  # method names, a rule, then the trait names
        CW = min(CELL_MAX, (W - X0 - sum(gaps(cols))) / len(cols))
        heads = [T.wrap(t, CW - 4, 13) for t in traits]
        slant = max(T.width(w, 13) for t in traits for w in t.split()) > CW - 4  # a word wider than its column
        # the values, in the largest size that fits every cell
        texts = [fmtv(r[i][j]) for i, j in drawn if r[i][j] is not None]
        vsize = next((sz for sz in (13.0, th.MIN_TEXT) if max((T.width(t, sz) for t in texts), default=0) <= CW - 6),
                     None)
        show = values and vsize is not None
        spans = {(i, j): f"[{fmtv(cis[i][j][0])}, {fmtv(cis[i][j][1])}]" for i, j in drawn if cis and cis[i][j]}
        both = show and intervals and max((T.width(s, th.MIN_TEXT) for s in spans.values()), default=0) <= CW - 4
        if intervals and not both:
            warnings.warn(f"viz: the intervals don't fit cells {CW:.0f} px wide, so they are left out; use a wider "
                          "size, fewer traits or methods, or leave the intervals for the text", stacklevel=2)
        CH = CELL_H_TWO if both else CELL_H

        def offsets(idx: list[int], size: float) -> dict[int, float]:  # where each row or column starts
            return {k: i * size + sum(gaps(idx)[:i]) for i, k in enumerate(idx)}
        xo, yo = offsets(cols, CW), offsets(rows, CH)

        def span(off: dict[int, float], size: float, b: int) -> tuple[float, float]:  # method block b's extent
            ks = [k for k in off if k // nt == b]
            return off[ks[0]], off[ks[-1]] + size

        # the key: the color bar, then what the box and the hatching mean
        def swatch(extra) -> str:
            return S.rect(0, 1, 13, 13, th.diverging(high, 0.0)) + extra
        key = [_colorbar(-1.0, 1.0, 0.0, fill_of, "Correlation", lambda v: SC.fmt_num(v), W)]
        key.append((swatch(S.rect(0.75, 1.75, 11.5, 11.5, "none", extra=f'stroke="{th.INK}" stroke-width="1.5"')), 0, 15))
        if zero:
            key.append((swatch(_hatch(0, 1, 13, 13, th.text_on(th.diverging(high, 0.0)))), 0, 15))
        labels = ["Same trait, different methods"] + (["Interval includes zero"] if zero else [])
        for k, lab in enumerate(labels, len(key) - len(labels)):
            svg_, _, h = key[k]
            key[k] = (svg_ + S.text(21, 12, lab, th.LEGEND_SIZE, th.INK2), 21 + T.width(lab, th.LEGEND_SIZE), h)
        if rel:
            lab = "Reliability in parentheses"
            key.append((S.text(0, 12, lab, th.LEGEND_SIZE, th.INK2), T.width(lab, th.LEGEND_SIZE), 15))
        key_svg, key_h = _key(key, W)
        out = [key_svg]
        Y0 = key_h + 22

        # rows: each method beside its block with a rule, then the traits
        for b, m in enumerate(methods):
            a, z = span(yo, CH, b)
            out.append(S.text(mw, Y0 + (a + z) / 2 + 4.5, m, 12.5, th.MUTED, "end"))
            out.append(S.line(mw + 9, Y0 + a, mw + 9, Y0 + z, th.GRID))
        for i in rows:
            out.append(S.text(X0 - 12, Y0 + yo[i] + CH / 2 + 4.5, traits[i % nt], 13.5, th.INK2, "end"))

        # the cells
        empty = th.mix(th.SURFACE, th.BG, 0.5)
        for i in rows:
            if rel:  # the diagonal: each measure's reliability
                x, y = X0 + xo[i], Y0 + yo[i]
                out.append(S.rect(x, y, CW, CH, empty))
                if rel[i] is not None:
                    out.append(S.text(x + CW / 2, y + CH / 2 + 4.5, f"({fmtv(rel[i])})", 13, th.INK2, "middle"))
        for i, j in drawn:
            x, y, v = X0 + xo[j], Y0 + yo[i], r[i][j]
            if v is None:
                out.append(S.rect(x, y, CW, CH, empty))
                out.append(S.text(x + CW / 2, y + CH / 2 + 4.5, "–", 13, th.MUTED, "middle"))
                continue
            f = fill_of(v)
            out.append(S.rect(x, y, CW, CH, f))
            hatched = (i, j) in zero
            if hatched:
                out.append(_hatch(x, y, CW, CH, th.text_on(f)))
            if show:
                halo = f if hatched else None  # the value stays clear of the hatching
                if both and (i, j) in spans:
                    out.append(S.text(x + CW / 2, y + CH / 2 - 2.5, fmtv(v), vsize, th.text_on(f), "middle", halo=halo))
                    out.append(S.text(x + CW / 2, y + CH / 2 + 13, spans[(i, j)], th.MIN_TEXT,
                                      th.text_on(f, soft=True), "middle", halo=halo))
                else:
                    out.append(S.text(x + CW / 2, y + CH / 2 + 4.5, fmtv(v), vsize, th.text_on(f), "middle", halo=halo))
            if i // nt != j // nt and i % nt == j % nt:  # the validity diagonal: same trait, different methods
                out.append(S.rect(x + 0.75, y + 0.75, CW - 1.5, CH - 1.5, "none",
                                  extra=f'stroke="{th.INK}" stroke-width="1.5"'))

        # columns, under the matrix: the traits (slanted when a name is wider than its column), then each method
        # under its block with a rule above it
        yb = Y0 + yo[rows[-1]] + CH
        cos, sin = math.cos(math.radians(40)), math.sin(math.radians(40))
        if slant:
            for j in cols:
                x = X0 + xo[j] + CW / 2 + 4
                out.append(f'<text transform="translate({S.n(x)},{S.n(yb + 14)}) rotate(-40)" text-anchor="end" '
                           f'{S.font_attrs(13, "sans", 400, False, th.INK2)}>{S.esc(traits[j % nt])}</text>')
            yl = yb + 14 + max(T.width(traits[j % nt], 13) for j in cols) * sin + 8
        else:
            nl = max(len(heads[j % nt]) for j in cols)
            for j in cols:
                for k, ln in enumerate(heads[j % nt]):
                    out.append(S.text(X0 + xo[j] + CW / 2, yb + 18 + k * 16, ln, 13, th.INK2, "middle"))
            yl = yb + 18 + (nl - 1) * 16 + 10
        for b, m in enumerate(methods):
            a, z = span(xo, CW, b)
            out.append(S.line(X0 + a, yl, X0 + z, yl, th.GRID))
            out.append(S.text(X0 + (a + z) / 2, yl + 17, m, 12.5, th.MUTED, "middle"))
        return Body("".join(out), yl + 22)

    return Figure(render, title=title, subtitle=subtitle, legend=False, width=width, kind="mtmm")


def describe(data, traits, methods, ci=None, decimals=None, fmt=None, **_) -> str:
    """Alt text: the traits and methods, every validity correlation, and the range of each kind of correlation."""
    traits, methods = [str(t) for t in traits], [str(m) for m in methods]
    nt, n = len(traits), len(traits) * len(methods)
    shape = "one row and column per trait under each method"
    r = _square(data, n, "data", shape)
    cis = _intervals(ci, n, shape)
    pairs = [(i, j) for i in range(n) for j in range(i) if r[i][j] is not None]  # each pair once
    f = SC.formatter(fmt, decimals, "", False, [r[i][j] for i, j in pairs])

    def spread(cells) -> str:
        vals = [r[i][j] for i, j in cells]
        return f"from {f(min(vals))} to {f(max(vals))}" if vals else "none"
    validity = [(i, j) for i, j in pairs if i % nt == j % nt]
    same = [(i, j) for i, j in pairs if i // nt == j // nt]
    cross = [(i, j) for i, j in pairs if i // nt != j // nt and i % nt != j % nt]
    out = [f"Multitrait-multimethod matrix: {nt} traits ({', '.join(traits)}), each measured by {len(methods)} "
           f"methods ({', '.join(methods)}).",
           "Same trait, different methods: " + "; ".join(f"{traits[i % nt]}, {methods[j // nt]} and "
                                                         f"{methods[i // nt]} {f(r[i][j])}" for i, j in validity) + ".",
           f"Different traits, same method: {spread(same)}.", f"Different traits, different methods: {spread(cross)}."]
    if cis:
        zero = sum(1 for i, j in pairs if cis[i][j] and cis[i][j][0] <= 0 <= cis[i][j][1])
        out.append(f"The interval includes zero for {zero} of {len(pairs)} correlations.")
    return " ".join(out)
