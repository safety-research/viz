"""Color roles: named conditions keep one color in every figure, and everything else is muted."""
from __future__ import annotations

import json
import re

import pytest

import vellum as vl
from vellum import colors
from vellum import theme as th

NAMES = {th.color(c).upper(): c for c in ("coral", "blue", "sage", "plum", "ochre", "gray", "gray-light", "gray-dark",
                                          "dark", "mid", "light-blue", "navy", "olive")}


def drawn(fig) -> list[str]:
    """Palette colors of the marks, in drawing order (ramp colors show as their hex)."""
    ramp = {c.upper() for n in range(2, 7) for c in th.ramp(n)}
    out = []
    for f in re.findall(r'fill="(#[0-9A-Fa-f]{6})"', fig.svg()):
        if f.upper() in NAMES:
            out.append(NAMES[f.upper()])
        elif f.upper() in ramp:
            out.append(f.upper())
    return out


@pytest.fixture(autouse=True)
def no_roles():
    vl.set_roles()
    yield
    vl.set_roles()


DATA = {"Closed book": 59, "Longer prompt": 55, "With search": 12}


def test_roles_color_the_named_conditions_and_mute_the_rest():
    assert drawn(vl.hbar(DATA)) == ["blue", "blue", "blue"]
    vl.set_roles(control="Closed book", intervention="With search")
    assert drawn(vl.hbar(DATA)) == ["gray", "gray", "coral"]
    assert drawn(vl.bars(DATA)) == ["gray", "gray", "coral"]
    assert vl.roles() == {"Closed book": "control", "With search": "intervention"}
    vl.set_roles(baseline="Closed book")  # another name for the control
    assert vl.roles() == {"Closed book": "control"}


def test_the_interventions_take_the_palette_in_order():
    data = {"Closed book": 60, "With search": 50, "Rerank": 40, "Prompting": 30, "Fine-tuning": 20, "Both": 10}
    f = vl.hbar(data, roles={"control": "Closed book", "intervention": "With search", "second": "Rerank",
                             "third": "Prompting", "fourth": "Fine-tuning", "fifth": "Both"})
    assert drawn(f) == ["gray", "coral", "blue", "sage", "plum", "ochre"]
    assert vl.color("intervention") == th.color("coral") and vl.color("baseline") == th.color("gray")


def test_ordered_conditions_run_light_to_dark():
    f = vl.bars({"0": 31, "1M": 26, "3M": 21, "10M": 17}, roles={"ordered": ["0", "1M", "3M", "10M"]})
    ramp = {c.upper() for c in th.ramp(4)}
    got = [c.upper() for c in re.findall(r'fill="(#[0-9A-Fa-f]{6})"', f.svg()) if c.upper() in ramp]
    assert got == [c.upper() for c in th.ramp(4)]
    lum = [th.luminance(c) for c in got]
    assert lum == sorted(lum, reverse=True)  # lightest first


def test_roles_apply_to_series_names_and_muted_series_take_shades():
    vl.set_roles(control="Closed book", intervention="With search")
    grouped = vl.bars({"Model A": [40, 10]}, series=["With search", "Closed book"], legend=False)
    assert drawn(grouped) == ["coral", "gray"]  # by name, not by position
    lines = vl.line({"Closed book": [1, 2], "Rerank": [2, 3], "Prompting": [2, 2], "With search": [3, 4]}, x=[0, 1],
                    legend=False, markers=False)
    strokes = {NAMES.get(c.upper()) for c in re.findall(r'stroke="(#[0-9A-Fa-f]{6})"', lines.svg())}
    assert {"gray", "gray-light", "coral"} <= strokes


def test_a_figure_keeps_the_roles_it_was_made_with():
    vl.set_roles(control="Closed book")
    f = vl.hbar(DATA)
    vl.set_roles(control="With search")
    assert drawn(f)[0] == "gray" and drawn(f)[2] == "gray" and drawn(f) == ["gray", "gray", "gray"]


def test_per_chart_roles_add_to_the_global_ones():
    vl.set_roles(control="Closed book", intervention="With search")
    assert drawn(vl.hbar(DATA, roles={"second": "Longer prompt"})) == ["gray", "blue", "coral"]
    with pytest.raises(ValueError, match="unknown role"):
        vl.hbar(DATA, roles={"focus": "With search"})


def test_explicit_colors_win_and_highlight_only_bolds_when_roles_are_in_play():
    vl.set_roles(control="Closed book")
    assert drawn(vl.hbar(DATA, colors={"Closed book": "navy"})) == ["navy", "gray", "gray"]
    f = vl.bars(DATA, highlight="Longer prompt")
    assert drawn(f) == ["gray", "gray", "gray"]
    assert re.search(r'font-weight="600"[^>]*>Longer prompt<', f.svg())
    vl.set_roles()
    assert drawn(vl.hbar(DATA, highlight="With search")) == ["gray", "gray", "blue"]  # no roles: the accent


def test_panels_pass_their_roles_to_each_panel():
    p = vl.panels([vl.bars({"Closed book": 38, "Search": 10}), vl.bars({"Small model": 38, "Search": 12})],
                  roles={"control": ["Closed book", "Small model"], "intervention": "Search"})
    assert drawn(p) == ["gray", "coral", "gray", "coral"]


def test_json_specs_take_roles():
    f = vl.from_spec({"chart": "hbar", "data": {"Base model": 31, "Worked examples": 18, "Forum answers": 37},
                      "roles": {"control": "Base model", "intervention": "Worked examples"}})
    assert drawn(f) == ["gray", "coral", "gray"]


def test_a_roles_file_sets_the_roles_for_every_script(tmp_path, monkeypatch):
    (tmp_path / "vellum-roles.json").write_text(json.dumps({"control": "Closed book", "intervention": ["With search"]}))
    work = tmp_path / "figures"
    work.mkdir()
    monkeypatch.chdir(work)
    colors._state.update(loaded=False, source=None)  # a fresh process
    colors._global.clear()
    assert drawn(vl.hbar(DATA)) == ["gray", "gray", "coral"]
    assert colors.source() == (tmp_path / "vellum-roles.json").resolve()
    vl.set_roles(intervention="Longer prompt")  # code replaces the file for this script
    assert drawn(vl.hbar(DATA)) == ["gray", "coral", "gray"] and colors.source() is None


def test_several_series_without_roles_take_the_default_order():
    f = vl.bars({"A": [1, 2, 3, 4, 5, 6, 7]}, series=list("abcdefg"), legend=False)
    assert drawn(f) == [*th.SERIES, "gray", "gray-light"]


def test_role_names_that_almost_match_are_flagged():
    vl.set_roles(control="Closed book", intervention="With search")
    near = vl.hbar({"Closed book": 59, "With search (n=400)": 12}, title="Search cut errors")
    assert any('"With search (n=400)" has no role' in p for p in near.check())
    none = vl.hbar({"Baseline": 59, "Search": 12}, title="Search cut errors")
    assert any("none of this figure's labels has one" in p for p in none.check())


def test_palettes_are_exported():
    assert vl.PALETTES["roles"] == {"control": "gray", "intervention": "coral", "second": "blue", "third": "sage",
                                    "fourth": "plum", "fifth": "ochre"}
    assert vl.PALETTES["outcomes"]["bad"] == "coral" and vl.PALETTES["series"][:3] == ["coral", "blue", "sage"]
