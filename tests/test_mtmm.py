"""The multitrait-multimethod matrix (issue #3). Everything here composes SVG without a browser."""
from __future__ import annotations

import re

import pytest

import viz as vl
from viz.charts.heatmap import CELL_H, CELL_H_TWO

TRAITS, METHODS = ["Sycophancy", "Honesty"], ["Self-report", "Probe"]
# rows and columns: Self-report Sycophancy, Self-report Honesty, Probe Sycophancy, Probe Honesty
R = [[1.0, -0.5, 0.6, -0.1],
     [-0.5, 1.0, 0.05, 0.7],
     [0.6, 0.05, 1.0, -0.3],
     [-0.1, 0.7, -0.3, 1.0]]
CI = [[(v - 0.15, v + 0.15) for v in row] for row in R]  # includes zero for 0.05 and -0.1 only


def body(fig) -> str:
    return fig.body(960).svg


def cells(svg: str) -> int:
    return len(re.findall(rf'<rect [^>]*height="({CELL_H}|{CELL_H_TWO})"', svg))


def outlines(svg: str) -> int:  # the validity diagonal's boxes, not the key's swatch
    return len(re.findall(r'<rect [^>]* fill="none" stroke="[^"]+" stroke-width="1.5"', svg)) - 1


def hatched(svg: str) -> int:  # hatched cells, not the key's swatch
    return len(re.findall(r'<path [^>]*stroke-opacity="0.3"', svg)) - ("Interval includes zero" in svg)


def test_the_lower_triangle_draws_each_pair_once_and_the_full_matrix_both_halves():
    lower = body(vl.mtmm(R, traits=TRAITS, methods=METHODS))
    assert cells(lower) == 6 and outlines(lower) == 2
    full = body(vl.mtmm(R, traits=TRAITS, methods=METHODS, triangle="full"))
    assert cells(full) == 12 and outlines(full) == 4
    assert "Same trait, different methods" in lower and ">0.60<" in lower and ">0.70<" in lower  # one precision


def test_without_a_diagonal_the_empty_first_row_and_last_column_are_dropped():
    lower = vl.mtmm(R, traits=TRAITS, methods=METHODS, decimals=2)
    kept = vl.mtmm(R, traits=TRAITS, methods=METHODS, decimals=2, reliabilities=[0.8, 0.9, 0.85, 0.95])
    svg = body(kept)
    assert all(f">({v})<" in svg for v in ("0.80", "0.90", "0.85", "0.95")) and "Reliability in parentheses" in svg
    assert cells(svg) == 6 + 4  # the pairs and the diagonal
    assert lower.body(960).height < kept.body(960).height
    assert svg.count(">Sycophancy<") == body(lower).count(">Sycophancy<") + 1  # row 1 back; the last column was Honesty


def test_reliabilities_take_a_list_or_a_mapping():
    forms = [[0.8, 0.9, 0.85, 0.95], {("Self-report", "Sycophancy"): 0.8, ("Self-report", "Honesty"): 0.9,
                                      ("Probe", "Sycophancy"): 0.85, ("Probe", "Honesty"): 0.95},
             {"Self-report": {"Sycophancy": 0.8, "Honesty": 0.9}, "Probe": {"Sycophancy": 0.85, "Honesty": 0.95}}]
    svgs = {body(vl.mtmm(R, traits=TRAITS, methods=METHODS, reliabilities=f)) for f in forms}
    assert len(svgs) == 1
    with pytest.raises(ValueError, match="one value per row"):
        vl.mtmm(R, traits=TRAITS, methods=METHODS, reliabilities=[0.8]).svg()


def test_cells_whose_interval_includes_zero_are_hatched():
    pairs = body(vl.mtmm(R, traits=TRAITS, methods=METHODS, ci=CI))
    lo = [[a for a, _ in row] for row in CI]
    hi = [[b for _, b in row] for row in CI]
    assert hatched(pairs) == 2 and "Interval includes zero" in pairs
    assert body(vl.mtmm(R, traits=TRAITS, methods=METHODS, ci=(lo, hi))) == pairs
    assert "Interval includes zero" not in body(vl.mtmm(R, traits=TRAITS, methods=METHODS))


def test_values_with_their_intervals_and_the_color_bar_without_values():
    svg = body(vl.mtmm(R, traits=TRAITS, methods=METHODS, ci=CI, intervals=True, decimals=2))
    assert ">0.05<" in svg and ">[−0.10, 0.20]<" in svg
    bare = body(vl.mtmm(R, traits=TRAITS, methods=METHODS, values=False))
    assert ">0.60<" not in bare and ">0.60<" in body(vl.mtmm(R, traits=TRAITS, methods=METHODS))
    assert all(f">{t}<" in bare for t in ("Correlation", "0", "1"))  # the color bar, with or without values


def test_intervals_that_do_not_fit_are_left_out_with_a_warning():
    fig = vl.mtmm(R, traits=TRAITS, methods=METHODS, ci=CI, intervals=True, decimals=2, width=300)
    with pytest.warns(UserWarning, match="don't fit"):
        svg = fig.svg()
    assert "[−0.10, 0.20]" not in svg


def test_a_missing_correlation_is_an_empty_cell():
    r = [row[:] for row in R]
    r[2][1] = r[1][2] = None
    svg = body(vl.mtmm(r, traits=TRAITS, methods=METHODS))
    assert cells(svg) == 6 and ">–<" in svg


def test_bad_input_says_what_is_expected():
    with pytest.raises(ValueError, match="4 by 4: one row and one column per trait under each method"):
        vl.mtmm(R[:3], traits=TRAITS, methods=METHODS)
    with pytest.raises(ValueError, match="two or more traits and two or more methods"):
        vl.mtmm([[1.0, 0.2], [0.2, 1.0]], traits=TRAITS, methods=["Self-report"])
    with pytest.raises(ValueError, match="'lower' or 'full'"):
        vl.mtmm(R, traits=TRAITS, methods=METHODS, triangle="upper")
    with pytest.raises(ValueError, match="pass ci="):
        vl.mtmm(R, traits=TRAITS, methods=METHODS, intervals=True)


def test_specs_and_alt_text():
    fig = vl.mtmm(R, traits=TRAITS, methods=METHODS, ci=CI)
    spec = vl.from_spec({"chart": "mtmm", "data": R, "traits": TRAITS, "methods": METHODS, "ci": CI})
    assert body(spec) == body(fig)
    alt = fig.alt_text()
    assert "Same trait, different methods: Sycophancy, Self-report and Probe 0.60; Honesty, Self-report and Probe 0.70." in alt
    assert "Different traits, same method: from −0.50 to −0.30." in alt and "includes zero for 2 of 6" in alt


def test_numpy_arrays_work_as_the_matrix_and_the_intervals():
    np = pytest.importorskip("numpy")
    fig = vl.mtmm(R, traits=TRAITS, methods=METHODS, ci=CI)
    assert body(vl.mtmm(np.array(R), traits=TRAITS, methods=METHODS, ci=np.array(CI))) == body(fig)
    lo, hi = np.array(CI)[..., 0], np.array(CI)[..., 1]
    assert body(vl.mtmm(np.array(R), traits=TRAITS, methods=METHODS, ci=(lo, hi))) == body(fig)
