"""Color roles: named conditions keep one color in every figure, and everything else is muted."""
from __future__ import annotations

import re

import pytest

import vellum as vl
from vellum import theme as th

NAMES = {th.color(c).upper(): c for c in ("coral", "blue", "sage", "gray", "dark", "light-blue", "navy", "clay")}


def drawn(fig) -> list[str]:
    """Palette colors of the marks, in drawing order."""
    return [NAMES[f.upper()] for f in re.findall(r'fill="(#[0-9A-Fa-f]{6})"', fig.svg()) if f.upper() in NAMES]


@pytest.fixture(autouse=True)
def no_roles():
    vl.set_roles()
    yield
    vl.set_roles()


DATA = {"Closed book": 59, "Longer prompt": 55, "With search": 12}


def test_roles_color_the_named_conditions_and_mute_the_rest():
    assert drawn(vl.hbar(DATA)) == ["blue", "blue", "blue"]
    vl.set_roles(baseline="Closed book", intervention="With search")
    assert drawn(vl.hbar(DATA)) == ["coral", "gray", "blue"]
    assert drawn(vl.bars(DATA)) == ["coral", "gray", "blue"]
    assert vl.roles() == {"Closed book": "baseline", "With search": "intervention"}


def test_roles_apply_to_series_names():
    vl.set_roles(baseline="Closed book", intervention="With search")
    grouped = vl.bars({"Model A": [40, 10]}, series=["With search", "Closed book"], legend=False)
    assert drawn(grouped) == ["blue", "coral"]  # by name, not by position
    lines = vl.line({"Closed book": [1, 2], "Rerank": [2, 3], "With search": [3, 4]}, x=[0, 1], legend=False)
    assert set(drawn(lines)) == {"coral", "gray", "blue"}


def test_a_figure_keeps_the_roles_it_was_made_with():
    vl.set_roles(baseline="Closed book")
    f = vl.hbar(DATA)
    vl.set_roles(baseline="With search")
    assert drawn(f)[0] == "coral" and drawn(f)[2] == "gray"


def test_per_chart_roles_add_to_the_global_ones():
    vl.set_roles(baseline="Closed book", intervention="With search")
    f = vl.hbar(DATA, roles={"second": "Longer prompt"})
    assert drawn(f) == ["coral", "sage", "blue"]
    with pytest.raises(ValueError, match="unknown role"):
        vl.hbar(DATA, roles={"focus": "With search"})


def test_explicit_colors_win_and_highlight_marks_labels_without_a_role():
    vl.set_roles(baseline="Closed book")
    assert drawn(vl.hbar(DATA, colors={"Closed book": "navy"})) == ["navy", "gray", "gray"]
    assert drawn(vl.hbar(DATA, highlight="With search")) == ["coral", "gray", "blue"]


def test_panels_pass_their_roles_to_each_panel():
    p = vl.panels([vl.bars({"Closed book": 38, "Search": 10}), vl.bars({"Small model": 38, "Search": 12})],
                  roles={"baseline": ["Closed book", "Small model"], "intervention": "Search"})
    assert drawn(p) == ["coral", "blue", "coral", "blue"]


def test_json_specs_take_roles():
    f = vl.from_spec({"chart": "hbar", "data": {"Base model": 31, "Worked examples": 18, "Forum answers": 37},
                      "roles": {"reference": "Base model", "intervention": "Worked examples"}})
    assert drawn(f) == ["dark", "blue", "gray"]


def test_several_series_without_roles_take_the_default_order():
    f = vl.bars({"A": [1, 2, 3, 4, 5, 6, 7]}, series=list("abcdefg"), legend=False)
    assert drawn(f) == [*th.SERIES, "gray"]


def test_palettes_are_exported():
    assert vl.PALETTES["roles"] == {"baseline": "coral", "intervention": "blue", "second": "sage", "reference": "dark"}
    assert vl.PALETTES["muted"] == "gray" and vl.PALETTES["series"][:3] == ["coral", "blue", "sage"]
