"""The built-in checks flag what breaks the house rules and stay quiet on figures that follow them."""
from __future__ import annotations

import re

import pytest

import viz as vl
from viz import checks


@pytest.fixture(autouse=True)
def fresh():
    checks.reset()
    vl.set_roles()
    yield
    checks.reset()
    vl.set_defaults(checks="warn")


def problems(title=None, subtitle=None, data=None, **kw) -> list[str]:
    return vl.hbar(data or {"Closed book": 59, "With search": 12}, title=title, subtitle=subtitle, **kw).check()


def test_a_plain_figure_passes():
    assert problems("With search, wrong answers fell from 59% to 12%") == []
    assert problems("With search, wrong answers fell from 59% to 12%", subtitle="Example data") == []
    assert problems("Search cut errors", subtitle="Example data; error bars are 95% intervals") == []


@pytest.mark.parametrize("title, phrase", [
    (None, "No title"),
    ("Search cut wrong answers for every one of the ten models we tested this week", "words"),
    ("Search helped; prompts did not", "semicolon"),
    ("The fix: search", "colon setup"),
    ("Did search help?", "question"),
    ("Search helped — a lot", "dash"),
    ("Search cut wrong answers.", "punctuation"),
    ("Search dramatically cut wrong answers", "dramatically"),
    ("Search cut far more errors than prompts", "far more"),
])
def test_title_rules(title, phrase):
    assert any(phrase in p for p in problems(title)), problems(title)


def test_subtitles_are_off_by_default():
    out = problems("Search cut errors", subtitle="GRPO, 100 steps, 2 seeds per arm")
    assert any("No subtitle by default" in p for p in out)


def test_extra_digits_are_flagged_unless_they_tell_values_apart():
    assert any("digits" in p for p in problems("Search cut errors", data={"A": 41.27, "B": 12.4}, decimals=2))
    assert problems("Search cut errors", data={"A": 38.5, "B": 38.2}, decimals=1) == []  # 38 and 38 would merge
    assert problems("Ratings rose", data={"A": 5.6, "B": 5.7}, unit="", decimals=1) == []


def test_too_many_accents_and_confusable_colors():
    data = {k: v for k, v in zip("ABCDE", [5, 4, 3, 2, 1])}
    many = problems("Five conditions differed", data=data, colors=["coral", "blue", "sage", "navy", "clay"])
    assert any("accent colors" in p for p in many)
    redgreen = problems("Two conditions differed", data={"A": 2, "B": 1}, colors=["#D62728", "#2CA02C"])
    assert any("look alike" in p for p in redgreen)


def test_a_condition_that_changes_color_between_figures_is_flagged():
    first = vl.hbar({"With search": 12, "Closed book": 59}, highlight="With search", title="Search cut errors")
    assert checks.check(first, name="fig1.png", record=True) == []
    second = vl.hbar({"With search": 12, "Rerank": 9}, colors={"With search": "sage"}, title="Rerank cut errors")
    out = checks.check(second, name="fig2.png", record=True)
    assert any('"With search" is sage here but orange in fig1.png' in p for p in out)


def test_panels_check_their_panel_titles():
    p = vl.panels([vl.bars({"A": 1, "B": 2}, title="(a) Prompts; no help")], title="Search cut errors")
    assert any(p_.startswith('Panel "(a) Prompts; no help"') for p_ in p.check())


def test_saving_warns_or_raises(tmp_path):
    f = vl.hbar({"A": 1, "B": 2}, title="Did search help?")
    with pytest.warns(checks.VizCheck, match="question"):
        f.save(tmp_path / "f.svg")
    vl.set_defaults(checks="error")
    with pytest.raises(checks.VizCheckError, match="question"):
        f.save(tmp_path / "g.svg")
    assert not (tmp_path / "g.svg").exists()
    vl.set_defaults(checks="off")
    f.save(tmp_path / "h.svg")


def test_the_gallery_follows_its_own_rules():
    from viz.gallery import figures
    for name, fig in figures().items():
        assert checks.check(fig, name=name, record=True) == [], name


def test_cli_check(tmp_path, capsys):
    import json

    from viz.cli import main
    spec = tmp_path / "s.json"
    spec.write_text(json.dumps([{"chart": "hbar", "data": {"A": 1}, "title": "Did it work?", "out": "a.png"},
                                {"chart": "hbar", "data": {"A": 1}, "title": "It worked"}]))
    assert main(["check", str(spec)]) == 1
    out = capsys.readouterr().out
    assert "a.png: Title is a question" in out and "figure 2" not in out


def test_one_color_must_mean_one_thing():
    p = vl.panels([vl.bars({"Year-old": 24, "Live": 10}), vl.bars({"Found nothing": 31}, colors={"Found nothing": "light-blue"})],
                  roles={"ordered": ["Year-old", "Live"]}, title="Errors fell as the index got fresher")
    assert any("share one color" in i for i in p.check())
    same_role = vl.hbar({"Closed book": 59, "Search": 12, "Small with search": 10},
                        roles={"baseline": "Closed book", "intervention": ["Search", "Small with search"]},
                        title="Search cut errors")
    assert not any("share one color" in i for i in same_role.check())


def test_categories_out_of_value_order_get_a_warning_not_a_change():
    out = vl.bars({"A": 10, "B": 30, "C": 20}, title="B led")
    assert any("aren't in order of their values" in p for p in out.check())
    assert re.findall(r">([ABC])<", out.svg()) == ["A", "B", "C"]  # nothing was reordered
    assert vl.bars({"A": 10, "B": 30, "C": 20}, title="B led", sort=True).check() == []
    assert vl.bars({"A": 10, "B": 30, "C": 20}, title="B led", sort=False).check() == []
    assert vl.hbar({"A": 10, "B": 20, "C": 30}, title="C led").check() == []  # already in order
    assert vl.bars({"Qwen3-8B": 10, "Qwen3-14B": 30, "Qwen3-32B": 20}, title="The 14B model led").check() == []
    assert vl.bars({"1M": 10, "3M": 30, "10M": 20}, title="3M led", roles={"ordered": ["1M", "3M", "10M"]}).check() == []
