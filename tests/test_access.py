"""Accessibility holds as numbers: text contrast, mark contrast, color-blind distances, text size, alt text."""
from __future__ import annotations

import itertools
import re

import pytest

import vellum as vl
from vellum import access
from vellum import theme as th
from vellum.colors import MUTED, ROLES


def test_ciede2000_matches_the_published_test_pairs():
    pairs = [((50.0, 2.6772, -79.7751), (50.0, 0.0, -82.7485), 2.0425),
             ((50.0, -1.3802, -84.2814), (50.0, 0.0, -82.7485), 1.0000),
             ((50.0, 2.5, 0.0), (73.0, 25.0, -18.0), 27.1492),
             ((60.2574, -34.0099, 36.2677), (60.4626, -34.1751, 39.4387), 1.2644),
             ((2.0776, 0.0795, -1.1350), (0.9033, -0.0636, -0.5514), 0.9082)]
    for a, b, want in pairs:
        assert access.delta_e_lab(a, b) == pytest.approx(want, abs=1e-3)


def test_contrast_and_simulation_endpoints():
    assert access.contrast("#000000", "#FFFFFF") == pytest.approx(21.0)
    for kind in access.CVD:
        assert access.simulate("#FFFFFF", kind) == "#FFFFFF"
        assert access.simulate("#000000", kind) == "#000000"
    # a pair everyone knows is hard for protanopes, and the classic safe pair
    assert access.worst_delta_e("#FF7F0E", "#2CA02C")[0] < 5
    assert access.worst_delta_e("#E69F00", "#56B4E9")[0] > 40


@pytest.mark.parametrize("token", ["INK", "INK2", "MUTED", "FAINT"])
def test_text_colors_reach_4_5_to_1(token):
    assert access.contrast(getattr(th, token), th.BG) >= 4.5


@pytest.mark.parametrize("name", [*ROLES.values(), *th.SERIES, "coral"])
def test_mark_colors_reach_3_to_1(name):
    assert access.contrast(th.color(name), th.BG) >= 3.0


def common_vision_distance(a: str, b: str) -> float:
    """CIEDE2000 for normal vision and the red-green color blindnesses (about 1 in 12 men)."""
    a, b = th.color(a), th.color(b)
    return min([access.delta_e(a, b)] + [access.delta_e(access.simulate(a, k), access.simulate(b, k))
                                         for k in ("protanopia", "deuteranopia")])


def test_the_control_and_first_three_interventions_stay_apart():
    group = ["dark", "coral", "blue", "sage", MUTED]
    for a, b in itertools.combinations(group, 2):
        assert common_vision_distance(a, b) >= 10, (a, b)
        assert access.worst_delta_e(th.color(a), th.color(b))[0] >= 6, (a, b)  # tritanopia too, a little closer


def test_the_fourth_and_fifth_only_near_their_hue_twins():
    # purple nears blue and ochre nears orange for red-green color-blind readers: the checks warn when they meet
    assert common_vision_distance("plum", "blue") < 10 and common_vision_distance("ochre", "coral") < 10
    for c in ("plum", "ochre"):
        twin = "blue" if c == "plum" else "coral"
        for other in ["dark", "coral", "blue", "sage", "plum", "ochre", MUTED]:
            if other not in (c, twin):
                assert common_vision_distance(c, other) >= 10, (c, other)


def test_muted_shades_and_the_ordered_ramp_stay_apart():
    # light grays can't be far apart and stay light; the shades help a legend, and labels carry the names
    for a, b in itertools.combinations(th.MUTED_SHADES, 2):
        assert access.worst_delta_e(th.color(a), th.color(b))[0] >= 5
    for n in range(2, 6):
        r = th.ramp(n)
        assert min(access.worst_delta_e(r[i], r[i + 1])[0] for i in range(n - 1)) >= 7


def test_text_on_any_fill_reaches_4_5_to_1():
    fills = [*th.PALETTE.values(), *th.TINT.values()]
    for lo, hi in th.SCALES.values():  # every step of the heatmap scales
        fills += [th.mix(lo, hi, k / 20) for k in range(21)]
    for f in fills:
        assert access.contrast(th.text_on(f), f) >= 4.5, f
        assert access.contrast(th.text_on(f, soft=True), f) >= 4.5, f


def test_strong_tiles_and_colored_labels_are_readable():
    for name in th.PALETTE:
        assert access.contrast("#FFFFFF", th.strong_fill(name)) >= 4.5, name
        assert access.contrast(th.readable(name), th.BG) >= 4.5, name


def test_no_gallery_text_is_smaller_than_the_minimum():
    from vellum.gallery import figures
    for name, fig in figures().items():
        sizes = [float(s) for s in re.findall(r'font-size="([\d.]+)"', fig.svg())]
        assert sizes and min(sizes) >= th.MIN_TEXT, f"{name}: {min(sizes)} px"


def test_alt_text_gives_the_title_and_the_data():
    f = vl.hbar({"Closed book": 59, "With search": 12}, title="With search, wrong answers fell from 59% to 12%",
                notes={"Closed book": "236 of 400"})
    alt = f.alt_text()
    assert alt.startswith("With search, wrong answers fell from 59% to 12%. Horizontal bar chart.")
    assert "Closed book 59% (236 of 400); With search 12%" in alt
    svg = f.svg()
    assert "<desc" in svg and "Closed book 59%" in svg and 'aria-labelledby="' in svg


def test_every_gallery_figure_has_alt_text_with_numbers():
    from vellum.gallery import figures
    for name, fig in figures().items():
        alt = fig.alt_text()
        assert len(alt) > len(fig.title or "") + 10, name
        if fig.kind not in ("quotes", "code_card", "episodes"):
            assert re.search(r"\d", alt), name
