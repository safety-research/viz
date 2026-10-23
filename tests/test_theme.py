"""The dark theme: every color switches and switches back, text keeps its contrast, and no color hides elsewhere."""
from __future__ import annotations

import re
from pathlib import Path

import pytest

import viz
from viz import access
from viz import theme as th


@pytest.fixture(autouse=True)
def light():
    yield
    viz.set_defaults(theme="light")


def state():
    return {k: getattr(th, k) for k in th._TOKENS}, dict(th.PALETTE), dict(th.TINT), dict(th.SCALES), th.RAMP


def test_dark_and_back_restores_every_color():
    before = state()
    viz.set_defaults(theme="dark")
    assert th.BG == "#0D1117" and state() != before
    viz.set_defaults(theme="light")
    assert state() == before
    with pytest.raises(ValueError):
        viz.set_defaults(theme="sepia")


def test_dark_text_and_marks_reach_their_contrast():
    viz.set_defaults(theme="dark")
    for ink in ("INK", "INK2", "MUTED", "FAINT"):
        for bg in ("BG", "CARD", "EP_CARD", "CODE_BG"):
            assert access.contrast(getattr(th, ink), getattr(th, bg)) >= 4.5, (ink, bg)
    for name in ("coral", "blue", "sage", "plum", "ochre"):
        assert access.contrast(th.color(name), th.BG) >= 3, name
    for name in ("deep-blue", "clay"):  # the code card's parameter and string colors
        assert access.contrast(th.readable(name, th.CARD_LIGHT), th.CARD_LIGHT) >= 4.5


def test_every_color_lives_in_the_theme():
    """A hex color written in a chart would stay the same in the dark theme."""
    src = Path(viz.__file__).parent
    for p in src.rglob("*.py"):
        if p.name not in ("theme.py", "access.py", "render.py"):
            assert not re.findall(r"[\"']#[0-9A-Fa-f]{6}[\"']", p.read_text()), p.name


def test_the_gallery_follows_its_own_rules_in_the_dark_theme():
    """Including after the light gallery: a theme's colors are compared only with that theme's earlier figures."""
    from viz import checks
    from viz.gallery import figures
    for name, fig in figures().items():
        checks.check(fig, name, record=True)
    viz.set_defaults(theme="dark")
    try:
        for name, fig in figures().items():
            assert checks.check(fig, name) == [], name
            assert th.BG in fig.svg()
    finally:
        checks.reset()
