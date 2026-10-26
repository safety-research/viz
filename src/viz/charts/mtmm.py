"""Multitrait-multimethod matrix (Campbell and Fiske, 1959): the correlations among several traits, each measured by
two or more methods. It is viz's one matrix (heatmap.grid) with the traits in method blocks, the validity diagonal
(same trait, different methods) boxed, and the correlations whose interval includes zero hatched."""
from __future__ import annotations

import math
import warnings
from collections.abc import Mapping

from .. import scale as SC
from .. import theme as th
from ..data import _is_frame
from ..figure import Body, Figure
from .heatmap import Cell, color_bar, grid, scale_color, scale_ends


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


def mtmm(data, *, traits, methods, ci=None, reliabilities=None, triangle="lower", values=True, intervals=False,
         decimals=None, fmt=None, scale="coral", domain=(0.0, 1.0), low="coral", high="blue", title=None,
         subtitle=None, width=None) -> Figure:
    """Multitrait-multimethod matrix: the correlations among several traits, each measured by two or more methods,
    the standard figure for convergent and discriminant validity (Campbell and Fiske, 1959), drawn as viz's matrix.

    data: the square correlation matrix in method blocks: every trait under the first method, then every trait under
    the second, and so on, with the traits in the same order in each block; a 2-D list, a numpy array or a DataFrame.
    traits, methods: their names, in that order. The diagonal is left out, or shows reliabilities= in parentheses:
    a list in the matrix's order, {(method, trait): value} or {method: {trait: value}}.
    ci: each correlation's interval, as (low, high) matrices or a matrix of (low, high) pairs. A cell whose interval
    includes zero is hatched, and intervals=True writes each interval under its value when it fits the cell.
    triangle: "lower" (the default) draws each pair once, below the diagonal; "full" draws the whole matrix.
    values: write each correlation in its cell.
    Colors are one tone, as in every viz matrix: domain=(0, 1) runs from a light tint at 0 to the deep end at 1, so
    a negative correlation takes the lightest tint and its number keeps the sign. Pass domain=(-1, 1) to shade the
    whole range, or scale="diverging" for orange below zero and blue above. The validity diagonal is boxed.
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
    lo, hi = domain
    fill_of = lambda v: scale_color(v, scale, lo, hi, 0.0, low, high)[0]

    def render(W: float) -> Body:
        trim = triangle == "lower" and not rel  # nothing on the diagonal: the first row and the last column are empty
        rows, cols = list(range(1 if trim else 0, n)), list(range(n - 1 if trim else n))
        at_row, at_col = {k: p for p, k in enumerate(rows)}, {k: p for p, k in enumerate(cols)}

        def blocks(idx: list[int]) -> list[tuple[str, int, int]]:  # each method's rows or columns
            spans = [(b, [p for p, k in enumerate(idx) if k // nt == b]) for b in range(nm)]
            return [(methods[b], ps[0], ps[-1]) for b, ps in spans if ps]
        empty = th.mix(th.SURFACE, th.BG, 0.5)
        cells = {}
        for k in rows if rel else ():  # the diagonal: each measure's reliability
            cells[(at_row[k], at_col[k])] = Cell(empty, None if rel[k] is None else f"({fmtv(rel[k])})", ink=th.INK2)
        for i, j in drawn:
            v = r[i][j]
            if v is None:
                cells[(at_row[i], at_col[j])] = Cell(empty, "–", ink=th.MUTED)
                continue
            second = f"[{fmtv(cis[i][j][0])}, {fmtv(cis[i][j][1])}]" if intervals and cis[i][j] else None
            cells[(at_row[i], at_col[j])] = Cell(fill_of(v), fmtv(v) if values else None, second=second,
                                                 boxed=i // nt != j // nt and i % nt == j % nt, hatched=(i, j) in zero)
        e0, e1 = scale_ends(scale, lo, hi, 0.0)
        key = [("box", "Same trait, different methods")] + ([("hatch", "Interval includes zero")] if zero else []) \
            + ([("text", "Reliability in parentheses")] if rel else [])
        body = grid(W, [traits[k % nt] for k in rows], [traits[k % nt] for k in cols], cells,
                    color_bar(e0, e1, fill_of, "Correlation", SC.tick_formatter([e0, e1])),
                    row_groups=blocks(rows), col_groups=blocks(cols), key=key,
                    swatch=fill_of(0.0 if scale == "diverging" else lo))
        if intervals and body.meta["second_left_out"]:
            warnings.warn("viz: the intervals don't fit these cells, so they are left out; use a wider size, fewer "
                          "traits or methods, or leave the intervals for the text", stacklevel=2)
        return body

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
