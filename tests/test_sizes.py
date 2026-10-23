"""Sizes: one width, plot height and print size per destination."""
from __future__ import annotations

import re

import pytest

import viz as vl
from viz import theme as th

DATA = {"Closed book": 59, "With search": 12}


@pytest.fixture(autouse=True)
def screen():
    yield
    vl.set_defaults(size="screen")


def attrs(svg: str) -> tuple[float, float, float, float]:
    w, h = (float(x) for x in re.search(r'<svg[^>]*?width="([\d.]+)"[^>]*?height="([\d.]+)"', svg).groups())
    vw, vh = (float(x) for x in re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"', svg).groups())
    return w, h, vw, vh


@pytest.mark.parametrize("name", list(th.SIZES))
def test_each_size_sets_the_width_and_the_printed_size(name):
    sz = th.SIZES[name]
    w, h, vw, vh = attrs(vl.bars(DATA, title="Search cut errors", size=name).svg())
    assert vw == pytest.approx(sz.width)
    if sz.inches:
        assert w == pytest.approx(sz.inches * 96) and h / w == pytest.approx(vh / vw, rel=1e-3)  # SVG numbers are rounded
    else:
        assert (w, h) == (vw, vh)


@pytest.mark.parametrize("name", list(th.SIZES))
def test_axis_charts_share_the_plot_height(name):
    sz = th.SIZES[name]
    for fig in (vl.bars(DATA, size=name), vl.line({"a": [1, 2, 3]}, x=[0, 1, 2], size=name)):
        assert fig.body(fig._width()).height == pytest.approx(sz.plot)
    sc = vl.scatter({"a": (1, 2), "b": (2, 3)}, size=name)
    assert sc.body(sc._width()).height == pytest.approx(sz.plot * 1.5)


def test_slides_fill_16_by_9_and_print_sizes_render_at_300_dpi():
    _, w, h = vl.bars(DATA, title="Search cut errors", size="slide").compose()
    assert (w, h) == (640, 360)
    assert vl.bars(DATA, size="paper")._png_scale() == pytest.approx(300 / 96)
    assert vl.bars(DATA, size="slide")._png_scale() == 3


def test_defaults_and_panels_follow_the_size():
    vl.set_defaults(size="column")
    f = vl.bars(DATA)
    assert f._width() == th.SIZES["column"].width - 2 * th.PAD_X
    p = vl.panels([vl.bars(DATA), vl.bars(DATA)], size="paper")
    assert attrs(p.svg())[0] == pytest.approx(6.75 * 96)
    with pytest.raises(ValueError, match="unknown size"):
        vl.bars(DATA, size="poster").svg()


def test_a_title_too_long_for_the_size_is_flagged():
    title = "With search, wrong answers fell from 59% to 12%"
    assert vl.hbar(DATA, title=title).check() == []
    assert any("lines at the column size" in p for p in vl.hbar(DATA, title=title, size="column").check())
