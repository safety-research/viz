"""Captions: a paper sets each figure's title and subtitle in its caption, so titles=False leaves them out of the image."""
from __future__ import annotations

import re

import pytest

import viz as vl

DATA = {"Closed book": 59, "With search": 12}
TITLE = "With search, wrong answers fell from 59% to 12%"
DRAWN = re.compile(r"<text[^>]*>With search, wrong")  # the title as drawn text, not the SVG's <title> for screen readers


@pytest.fixture(autouse=True)
def titles_drawn():
    yield
    vl.set_defaults(titles=True)


def test_titles_false_leaves_the_title_and_subtitle_for_the_caption():
    drawn = vl.hbar(DATA, title=TITLE, subtitle="Example data")
    left = vl.hbar(DATA, title=TITLE, subtitle="Example data", titles=False)
    svg = left.svg()
    assert DRAWN.search(drawn.svg()) and not DRAWN.search(svg) and "Example data" not in svg
    assert f">{TITLE}</title>" in svg and left.alt_text().startswith(TITLE + ".")
    assert left.compose()[2] < drawn.compose()[2]
    assert left.caption() == drawn.caption() == TITLE + ". Example data."


def test_set_defaults_leaves_titles_out_and_one_chart_can_draw_its_own():
    vl.set_defaults(titles=False)
    assert not DRAWN.search(vl.hbar(DATA, title=TITLE).svg())
    assert DRAWN.search(vl.hbar(DATA, title=TITLE, titles=True).svg())


def test_the_legend_and_panel_titles_stay_in_the_image():
    data = {"Model A": [12.5, 4.0], "Model B": [18.0, 5.5]}
    svg = vl.bars(data, series=["No system prompt", "Safety system prompt"], title=TITLE, titles=False).svg()
    assert ">Safety system prompt<" in svg and not DRAWN.search(svg)
    p = vl.panels([vl.hbar(DATA, title="Model A"), vl.hbar(DATA, title="Model B")], title=TITLE, titles=False)
    svg = p.svg()
    assert ">Model A<" in svg and ">Model B<" in svg and not DRAWN.search(svg)


def test_caption_sentences():
    f = vl.hbar(DATA, title=TITLE, subtitle="Example data · Error bars are 95% intervals")
    assert f.caption() == TITLE + ". Example data. Error bars are 95% intervals."
    assert vl.hbar(DATA, title="Did search help?").caption() == "Did search help?"
    assert vl.hbar(DATA).caption() == ""


def test_a_caption_title_has_no_line_to_fit_but_keeps_the_other_rules():
    assert any("lines at the column size" in p for p in vl.hbar(DATA, title=TITLE, size="column").check())
    assert not any("lines at" in p for p in vl.hbar(DATA, title=TITLE, size="column", titles=False).check())
    assert any("semicolon" in p for p in vl.hbar(DATA, title="Search helped; reranking helped more", titles=False).check())


def test_specs_take_titles():
    f = vl.from_spec({"chart": "hbar", "data": DATA, "title": TITLE, "titles": False})
    assert not DRAWN.search(f.svg()) and f.caption() == TITLE + "."
