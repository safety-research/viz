"""Smoke and behavior tests. SVG composition runs without a browser; a few tests render through Chromium."""
from __future__ import annotations

import json
import re
import warnings

import pytest

import viz as vl
from viz import scale as SC
from viz import text as T
from viz.gallery import figure, figures


def _size(svg: str) -> tuple[float, float]:
    m = re.search(r'<svg[^>]*width="([\d.]+)"[^>]*height="([\d.]+)"', svg)
    return float(m.group(1)), float(m.group(2))


@pytest.mark.parametrize("name", list(figures()))
def test_gallery_composes(name):
    svg = figures()[name].svg()
    w, h = _size(svg)
    assert w == 1008 and 150 < h < 2500
    assert "NaN" not in svg and "None" not in svg


def test_every_chart_is_in_the_registry():
    for k in ("hbar", "bars", "heatmap", "tiles", "waffle", "scatter", "dumbbell", "line", "stacked", "panels",
              "quotes", "episodes", "code_card"):
        assert k in vl.CHARTS


def test_hbar_inputs_and_options():
    a = vl.hbar({"a": 1, "b": 2}).svg()
    b = vl.hbar([("a", 1), ("b", 2)]).svg()
    assert a.count("<path") == b.count("<path") == 2
    g = vl.hbar({"x": [1, 2], "y": [3, 4]}, series=["s1", "s2"], ci={"x": [(0, 2), (1, 3)], "y": [None, (3, 5)]})
    svg = g.svg()
    assert "s1" in svg and "s2" in svg  # legend
    neg = vl.hbar({"up": 3, "down": -2}, unit="").svg()
    assert "−2" in neg  # true minus sign
    sec = vl.hbar([("a", 1), vl.section("Others"), ("b", 2)]).svg()
    assert "Others" in sec
    with pytest.raises(ValueError):
        vl.hbar([("a", 1), vl.section("x")], sort=True)
    with pytest.raises(ValueError):
        vl.hbar({"a": [1, 2], "b": [1]}).svg()


def _group_x(svg: str, label: str) -> float:
    """x of the top-level group that holds this text (the legend's, for a series name)."""
    return float(re.search(r'<g transform="translate\(([\d.]+),[\d.]+\)">(?:(?!<g ).)*?>' + re.escape(label) + "<", svg).group(1))


def test_hbar_legend_starts_where_the_bars_start():
    data = {"Small model": [62, 48], "Large model": [83, 64]}
    names = ["No hint", "Strong hint"]
    f = vl.hbar(data, series=names, title="Hints helped both sizes")
    svg = f.svg()
    bars_left = f.body(f._width()).meta["key_x"]
    first_gridline = float(re.search(r'<line x1="([\d.]+)"', svg).group(1))
    assert bars_left == pytest.approx(first_gridline, abs=0.01) and bars_left > 100
    assert _group_x(svg, "No hint") == pytest.approx(24 + bars_left, abs=0.01)  # 24: the figure's left padding
    assert re.search(r'<text[^>]*\bx="24"[^>]*>Hints helped', svg)  # the title stays at the left edge
    below = vl.hbar(data, series=names, legend_position="bottom").svg()
    assert _group_x(below, "No hint") == pytest.approx(24 + bars_left, abs=0.01)
    vl.set_defaults(theme="dark")
    try:
        assert _group_x(vl.hbar(data, series=names).svg(), "No hint") == pytest.approx(24 + bars_left, abs=0.01)
    finally:
        vl.set_defaults(theme="light")


def test_hbar_legend_stays_left_when_it_would_not_fit_beside_the_labels():
    data = {"Small model": [62, 48, 31], "Large model": [83, 64, 40]}
    wraps = ["No hint at all in the prompt given to the model", "A weak hint placed in the system prompt only",
             "A strong hint repeated in every single user turn"]  # one row at full width, two from the bars
    assert _group_x(vl.hbar(data, series=wraps).svg(), wraps[0]) == 24
    too_wide = ["No hint " + "x" * 150, "Weak hint", "Strong hint"]  # one entry wider than the plot
    assert _group_x(vl.hbar(data, series=too_wide).svg(), too_wide[0]) == 24


def test_only_hbar_moves_its_legend():
    data = {"Small model": [62, 48], "Large model": [83, 64]}
    names = ["No hint", "Strong hint"]
    assert _group_x(vl.bars(data, series=names).svg(), "No hint") == 24
    grid = vl.panels([vl.hbar(data, series=names, title="a"), vl.hbar(data, series=names, title="b")])
    assert _group_x(grid.svg(), "No hint") == 24


def test_long_labels_wrap_and_long_titles_wrap():
    label = "A very long label that would otherwise eat the whole chart and leave no room for the bars at all"
    svg = vl.hbar({label: 40, "short": 10}, title="T " * 80).svg()
    assert svg.count(">T T") >= 2  # title wrapped onto more than one line


def test_percent_warning_for_fractions():
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        vl.hbar({"a": 0.2, "b": 0.5})
        assert any("fractions" in str(x.message) for x in w)
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        vl.hbar({"a": 0.2, "b": 0.5}, unit="")


def test_bars_negative_grouped_ci_ref():
    svg = vl.bars({"a": [1.5, -0.5], "b": [-1.0, 2.0]}, series=["x", "y"], unit="", ci={"a": [(1, 2), (-1, 0)]},
                  ref=0.5, ylabel="Delta").svg()
    assert 'stroke-dasharray="4 4"' in svg and "Delta" in svg


def test_heatmap_scales_and_groups():
    data = {"r1": {"c1": -5, "c2": 10}, "r2": {"c1": 3, "c2": None}}
    svg = vl.heatmap(data, scale="diverging", unit="", col_groups=[("Both", ["c1", "c2"])]).svg()
    assert "Both" in svg and "–" in svg  # missing cell
    for sc in ("blue", "coral", "sage", "green"):
        vl.heatmap({"r": [10, 90]}, cols=["a", "b"], scale=sc).svg()


def test_domain_and_ticks():
    assert SC.domain([36.7], percent=True)[:2] == (0, 40)
    assert SC.domain([90.4], percent=True)[1] == 100
    lo, hi, tk = SC.domain([-0.316, 0.516])
    assert (lo, hi) == (-0.4, 0.6) and len(tk) == 6
    assert SC.fmt_num(-0.06, 2) == "−0.06" and SC.fmt_num(0.17, 2, signed=True) == "+0.17"
    assert SC.formatter(None, 1, "%")(0) == "0%"


def test_rich_text_wrap_keeps_glued_words():
    lines = T.wrap_rich("**Figure 1.** See `search_docs`. It works " * 6, 300, 14)
    assert all(lines) and lines[0][0].bold
    flat = ["".join(r.text for r in ln) for ln in lines]
    assert not any(f.startswith(".") for f in flat)  # a period never starts a line


def test_one_frame_and_older_scripts_still_run():
    f = vl.hbar({"a": 1, "b": 2}, title="Claim", subtitle="Measure")
    svg = f.svg()
    assert not re.search(r'<text[^>]*text-anchor="middle"[^>]*>Claim</text>', svg)  # a left-aligned claim title
    # older scripts passed frame="blog" or set it as a default: both still run and draw the one frame
    assert vl.hbar({"a": 1, "b": 2}, title="Claim", subtitle="Measure", frame="blog").svg() == svg
    vl.set_defaults(frame="blog")
    assert vl.hbar({"a": 1, "b": 2}, title="Claim", subtitle="Measure").svg() == svg
    with pytest.raises(TypeError):  # the house style has no caption under the figure
        vl.hbar({"a": 1}, caption="**Figure 1.** Caption.")


@pytest.mark.filterwarnings("ignore::viz.checks.VizCheck")  # bare test specs, not house-style figures
def test_from_spec_round_trip(tmp_path):
    specs = [
        {"chart": "hbar", "data": {"Closed book": 59, "With search": 12}, "highlight": "With search", "title": "t"},
        {"chart": "bars", "data": {"a": [1, 2]}, "series": ["x", "y"], "ci": {"a": [[0, 2], [1, 3]]}},
        {"chart": "heatmap", "data": {"r": {"c": 50}}},
        {"chart": "tiles", "grid": [[{"value": 3, "lines": ["x"], "color": "blue", "strong": True}]]},
        {"chart": "waffle", "parts": {"a": 3, "b": 1}},
        {"chart": "scatter", "points": {"a": [1, 2], "b": [2, 3]}, "labels": True, "trend": "fit"},
        {"chart": "dumbbell", "data": {"a": [1, 2]}, "unit": ""},
        {"chart": "line", "series": {"a": [1, 2, 3]}, "x": [0, 1, 2]},
        {"chart": "stacked", "data": {"a": [60, 40]}, "series": ["x", "y"]},
        {"chart": "panels", "figs": [{"chart": "hbar", "data": {"a": 1}}, {"chart": "hbar", "data": {"b": 2}}]},
        {"chart": "quotes", "replies": [{"label": "A", "text": "hi"}], "prompt": "q"},
        {"chart": "episodes", "items": [{"title": "E", "blocks": [["Label", "quote", "q"], ["", "code", "x == y"]],
                                         "outcome": ["done", "blue"]}]},
        {"chart": "code_card", "name": "f", "params": {"x": "y"}, "description": "d"},
    ]
    for s in specs:
        assert vl.from_spec(json.loads(json.dumps(s))).svg().startswith("<svg")
    p = tmp_path / "spec.json"
    p.write_text(json.dumps([dict(specs[0], out=str(tmp_path / "a.png")), dict(specs[4], out=str(tmp_path / "b.svg"))]))
    out = vl.render_file(p)
    assert [o.name for o in out] == ["a.png", "b.svg"] and all(o.stat().st_size > 1000 for o in out)


def test_exports(tmp_path):
    f = vl.hbar({"Closed book": 59, "With search": 12}, highlight="With search", title="Exports")
    png = f.save(tmp_path / "f.png")
    assert png.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
    from PIL import Image
    assert Image.open(png).size[0] == 2016  # 2x of 1008
    pdf = f.save(tmp_path / "f.pdf")
    assert pdf.read_bytes()[:5] == b"%PDF-"
    svg = f.save(tmp_path / "f.svg").read_text()
    assert "@font-face" in svg and "base64" in svg
    html = f.save(tmp_path / "f.html").read_text()
    assert "fonts.googleapis.com" in html and "<svg" in html
    assert f.png(scale=1)[:4] == b"\x89PNG"


@pytest.mark.parametrize("name", ["dotplot", "scatter", "episodes"])
def test_pdfs_embed_truetype_fonts_not_type3(name, tmp_path):
    """Venues reject Type 3 fonts, which is how Chromium writes variable fonts and stroked text (the halos behind
    labels). These figures have halos, a rotated axis label, italic serif and mono text."""
    data = figure(name).save(tmp_path / "f.pdf").read_bytes()
    assert b"/Type3" not in data and b"/CIDFontType2" in data


def test_unknown_color_message():
    with pytest.raises(ValueError, match="unknown color"):
        vl.hbar({"a": 1}, color="chartreuse").svg()


REBUILD = "run: viz gallery -o docs/gallery --examples examples/README.md --readme README.md"


def test_the_examples_page_is_generated_from_the_gallery():
    from pathlib import Path

    from viz.gallery import examples
    page = Path(__file__).resolve().parents[1] / "examples" / "README.md"
    assert page.read_text() == examples(), REBUILD


def test_the_readme_gallery_is_generated_and_every_template_has_its_image():
    from pathlib import Path

    from viz.gallery import EXAMPLES, ORDER, STEM, about, readme_gallery
    root = Path(__file__).resolve().parents[1]
    assert readme_gallery() in (root / "README.md").read_text(), REBUILD
    assert len(set(ORDER)) == len(ORDER)  # each template in one section
    assert sorted(p.stem for p in EXAMPLES.glob("*.py")) == sorted(STEM.values())  # and every script in a section
    assert all(about(n) != n for n in ORDER)  # each says what it is for
    for folder in ("gallery", "gallery/cards"):  # each template's figure and its card
        assert sorted(p.stem for p in (root / "docs" / folder).glob("*.png")) == sorted(STEM.values()), REBUILD


def test_alt_text_gives_line_values_at_marks_and_stacked_rows_in_drawn_order():
    roc = {"Probe": [(0, 0), (1, 52), (5, 80), (10, 88), (100, 100)],
           "Monitor": [(0, 0), (1, 18), (5, 41), (10, 55), (100, 100)]}
    alt = vl.line(roc, marks={5: "5% false positives"}, title="The probe caught 80% of hacks").alt_text()
    assert "At 5% false positives: Probe 80%, Monitor 41%." in alt
    long = vl.line({"a": [5, 9, 30, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2]}, title="a fell").alt_text()
    assert "from 5% at 0 to 2% at 13, highest 30% at 2" in long
    stacked = vl.stacked({"Coding": [61, 15, 24], "Sysadmin": [52, 17, 31]}, series=["Failed", "Unclear", "Claimed"],
                         sort="Claimed", title="Sysadmin led").alt_text()
    assert stacked.index("Sysadmin:") < stacked.index("Coding:")


def test_a_single_line_can_end_in_its_value_alone():
    f = vl.line({"Eval awareness": [2.1, 9.0, 18.5]}, x=[0, 1000, 2000], end_labels="value",
                title="Eval awareness rose from 2.1% to 18.5%")
    svg = f.svg()
    assert ">18.5%</tspan>" in svg and ">Eval awareness</tspan>" not in svg
