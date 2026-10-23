"""The pieces the README examples rely on: grouped scatter, log exponents, heatmap values that fit, the label font."""
from __future__ import annotations

import re

import pytest

import viz
from viz import theme as th


@pytest.fixture(autouse=True)
def serif():
    yield
    viz.set_defaults(font="serif")
    viz.set_roles()


def test_grouped_scatter_colors_each_group_and_has_a_legend():
    groups = {"Refusal": [(-1, -1), (-1.2, -0.8)], "Compliance": [(0, 1), (0.1, 1.2)]}
    f = viz.scatter(groups, title="Refusals sat apart from compliance")
    svg = f.svg()
    assert svg.count('fill-opacity="0.72"') == 4
    assert ">Refusal<" in svg and ">Compliance<" in svg  # the legend
    viz.set_roles(intervention="Compliance")
    assert th.color("coral") in viz.scatter(groups, legend=False).svg()
    assert "2 groups" in f.alt_text()


def test_log_axis_ticks_each_power_of_ten_with_a_raised_exponent():
    f = viz.line({"Large model": [30, 50, 70]}, x=[1e20, 1e21, 1e22], xscale="log", end_labels=False)
    svg = f.svg()
    assert len(re.findall(r'<tspan[^>]*dy="-[\d.]+"[^>]*>2[012]</tspan>', svg)) == 3


def test_heatmap_values_never_overflow_their_cells():
    data = {f"Model {c}": [86, 59, 89, 92, 71, 64, 77, 81] for c in "ABC"}
    cols = ["MMLU", "GPQA", "HellaSwag", "ARC", "TruthfulQA", "MATH", "HumanEval", "BBH"]
    svg = viz.heatmap(data, cols=cols, width=300).svg()
    assert "rotate(-50)" in svg  # long headers slant
    cells = re.findall(r"<text[^>]*>(\d+%?)</text>", svg)
    assert cells and not any(c.endswith("%") for c in cells)  # too narrow for "86%": the unit goes, never an overlap


def test_the_label_font_is_one_setting():
    f = viz.bars({"A": 1, "B": 2}, title="B led")
    assert th.FAMILIES["serif"] in f.svg() and th.FAMILIES["sans"] not in f.svg()
    viz.set_defaults(font="sans")
    assert th.FAMILIES["sans"] in f.svg()
    with pytest.raises(ValueError):
        viz.set_defaults(font="comic")
