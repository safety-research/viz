"""Tests for the distribution charts (dotplot, histogram, box, strip, ecdf) and the runs= overlays on bars, hbar
and line. Everything here composes SVG without a browser."""
from __future__ import annotations

import json
import math
import os
import re
import subprocess
import sys
from itertools import pairwise

import pytest

import viz as vl
from viz import theme as th
from viz.charts import dist

NAN = float("nan")
NEW = ("dotplot", "histogram", "box", "strip", "ecdf", "violin")


def examples() -> dict[str, vl.Figure]:
    """One figure per chart and option worth covering, built fresh on every call."""
    seconds = {"Closed book": [2.1, 2.8, 3.0, 3.3, 4.1, 2.6, 9.5], "With search": [5.2, 6.8, 7.4, 8.1, 9.9, 6.1, 22.0]}
    seeds = {"Plain fine-tune": [33.0, 35.5, 31.0, 36.0, 34.5], "Worked examples": [17.5, 21.0, 19.0, 18.0, 20.5]}
    return {
        "dotplot": vl.dotplot({"A": -8.5, "B": -12.5, "C": 3.0}, ci={"A": (-14, -3), "B": (-19, -6), "C": (-2, 8)},
                              ref=0, unit="", xlabel="Change", title="Dot plot"),
        "dotplot_grouped": vl.dotplot({"A": [30, 12], "B": [40, 15]}, series=["Closed book", "With search"],
                                      ci={"A": [(25, 35), (9, 15)], "B": [None, (12, 18)]}, notes={"B": "n = 40"}),
        "dotplot_sections": vl.dotplot([("A", 31.0), vl.section("Other data"), ("B", 27.4)], highlight="B", ref=31,
                                       ref_label="base"),
        "histogram": vl.histogram([1.5, 2.0, 2.2, 3.1, 3.3, 3.4, 4.8, 5.0, 7.5], xlabel="Seconds", ylabel="Answers"),
        "histogram_overlaid": vl.histogram(seconds, stat="percent", xlabel="Seconds"),
        "histogram_whole": vl.histogram([1, 2, 2, 3, 3, 3, 4, 4, 5, 7], values=True),
        "box": vl.box(seconds, unit="", ylabel="Seconds", colors={"Closed book": "coral"}),
        "box_points": vl.box(seconds, unit="", points=True),
        "box_horizontal": vl.box(seconds, unit="", horizontal=True, xlabel="Seconds"),
        "box_grouped": vl.box({"Model A": [[2, 3, 4, 12], [5, 6, 7]], "Model B": [[3, 4, 5], [6, 7, 8, 18]]},
                              series=["Closed book", "With search"], unit=""),
        "strip": vl.strip(seeds, ci=True, decimals=0, ylabel="Wrong answers"),
        "strip_horizontal": vl.strip(seeds, ci=True, horizontal=True, highlight="Worked examples"),
        "strip_grouped": vl.strip({"Model A": [[30, 31, 33], [10, 12, 14]], "Model B": [[38, 41], [14, 15, 17]]},
                                  series=["Closed book", "With search"]),
        "ecdf": vl.ecdf(seconds, ref=10, ref_label="10 seconds", xlabel="Seconds"),
        "ecdf_complementary": vl.ecdf(seconds, complementary=True, highlight="With search"),
        "violin": vl.violin(seconds, unit="", ylabel="Seconds", colors={"Closed book": "coral"}),
        "violin_width": vl.violin(seconds, unit="", scale="width", horizontal=True, xlabel="Seconds"),
        "violin_grouped": vl.violin({"Model A": [[2, 3, 4, 12], [5, 6, 7]], "Model B": [[3, 4, 5], [6, 7, 8, 18]]},
                                    series=["Closed book", "With search"], unit="", bandwidth=1.5),
        "bars_runs": vl.bars({k: sum(v) / len(v) for k, v in seeds.items()}, runs=seeds, ci={"Plain fine-tune": (31, 37)}),
        "bars_runs_grouped": vl.bars({"A": [30, 12], "B": [40, 15]}, series=["x", "y"],
                                     runs={"A": [[28, 31, 33], [10, 12, 14]], "B": [[38, 41, 42], None]}),
        "hbar_runs": vl.hbar({k: sum(v) / len(v) for k, v in seeds.items()}, runs=seeds, notes={"Worked examples": "5 runs"}),
        "line_runs": vl.line({"a": [3, 2, 1]}, x=[0, 1, 2], runs={"a": [[3.2, 2.1, 0.8], [2.9, 1.8, 1.3]]}, unit=""),
    }


def _floats(attr: str, svg: str) -> list[float]:
    return [float(v) for v in re.findall(rf' {attr}="(-?[\d.]+)"', svg)]


@pytest.mark.parametrize("name", list(examples()))
def test_renders_clean_svg(name):
    svg = examples()[name].svg()
    assert svg.startswith("<svg") and svg.endswith("</svg>")
    for bad in ("NaN", "nan", "None", "inf"):
        assert bad not in re.sub(r">[^<]*<", "><", svg), bad  # no broken numbers in any attribute


@pytest.mark.parametrize("name", list(examples()))
def test_deterministic(name):
    a, b = examples()[name], examples()[name]
    assert a.svg() == b.svg() == a.svg()  # fresh builds agree, and rendering twice changes nothing


def test_deterministic_across_processes():
    """Same input, same bytes, whatever the string hash seed (no set or dict ordering leaks into the output)."""
    here = os.path.dirname(__file__)
    code = (f"import hashlib, sys; sys.path.insert(0, {here!r}); from test_charts_more import examples; "
            "print(hashlib.sha256(''.join(f.svg() for f in examples().values()).encode()).hexdigest())")
    digests = set()
    for seed in ("1", "2"):
        env = dict(os.environ, PYTHONHASHSEED=seed)
        digests.add(subprocess.run([sys.executable, "-c", code], env=env, capture_output=True, text=True,
                                   check=True).stdout.strip())
    assert len(digests) == 1


def test_registered():
    for k in NEW:
        assert k in vl.CHARTS and k in vl.__all__ and callable(getattr(vl, k))


def test_none_and_nan_are_skipped():
    data = {"a": [1.0, None, 2.0, NAN, 3.0], "b": [None, NAN, 4.0, 5.0]}
    labels, vals, ns, _ = dist.samples(data)
    assert labels == ["a", "b"] and ns == 1 and vals == [[[1.0, 2.0, 3.0]], [[4.0, 5.0]]]
    for f in (vl.box(data, unit=""), vl.strip(data, unit="", ci=True), vl.ecdf(data), vl.histogram(data),
              vl.violin(data, unit=""), vl.dotplot({"a": 1.0, "b": None, "c": NAN}, unit="")):
        svg = f.svg()
        assert "NaN" not in svg and "None" not in svg
    empty = {"a": [None, NAN], "b": [1.0, 2.0]}  # a group with nothing left is skipped, not an error
    for f in (vl.box(empty, unit=""), vl.strip(empty, unit=""), vl.ecdf(empty), vl.histogram(empty),
              vl.violin(empty, unit="")):
        assert f.svg().startswith("<svg")
    # runs: missing values are dropped, missing bars still get their dots
    svg = vl.bars({"a": None, "b": 2.0}, runs={"a": [1.0, None, NAN, 3.0], "b": [2.0]}, unit="").svg()
    assert svg.count('stroke="#FFFFFF" stroke-width="1"') == 3
    with pytest.raises(ValueError, match="finite"):
        vl.box({"a": [1.0, math.inf]})


def test_single_group():
    for f in (vl.dotplot({"Only": 40}), vl.histogram([3, 4, 4, 5]), vl.box({"Only": [1, 2, 3, 4]}, unit=""),
              vl.strip({"Only": [31.0]}, ci=True), vl.ecdf({"Only": [1, 2, 3]}), vl.ecdf([1, 2, 3]),
              vl.box({"Only": [5, 5, 5]}, unit="", horizontal=True), vl.strip({"Only": [1, 2]}, horizontal=True),
              vl.violin({"Only": [1, 2, 2, 3, 7]}, unit=""), vl.violin({"Only": [4, 4, 4]}, unit="")):
        svg = f.svg()
        assert svg.startswith("<svg") and "NaN" not in svg
    # a named single curve is labeled directly; an unnamed one needs no label
    assert "Only" in vl.ecdf({"Only": [1, 2, 3, 4]}).svg()


def test_negative_values():
    svg = vl.dotplot({"A": -8.5, "B": 4.0}, ci={"A": (-14, -3), "B": (-1, 9)}, ref=0, unit="", decimals=1).svg()
    assert "−8.5" in svg and "4.0" in svg
    assert "−" in vl.box({"A": [-3, -2, -1, 0, 1]}, unit="").svg()
    assert "−" in vl.strip({"A": [-3.0, -2.0, 1.0]}, unit="").svg()
    assert "−" in vl.histogram([-3.2, -1.0, -0.5, 0.2, 1.4]).svg()
    assert "−" in vl.ecdf([-3.2, -1.0, -0.5, 0.2, 1.4]).svg()
    assert "−" in vl.bars({"a": -1.0}, runs={"a": [-1.5, -0.5]}, unit="").svg()
    assert "−" in vl.violin({"A": [-3.0, -2.5, -1.0, 0.5, 1.0]}, unit="").svg()


def test_json_spec_round_trip():
    specs = [
        {"chart": "dotplot", "data": {"A": -8.5, "B": -12.5}, "ci": {"A": [-14, -3], "B": [-19, -6]}, "ref": 0,
         "unit": ""},
        {"chart": "histogram", "data": [1, 2, 2, 3, 5, 8], "bins": 4},
        {"chart": "histogram", "data": {"x": [1, 2, 3], "y": [2, 3, 4]}, "stat": "percent", "bins": [0, 2, 4, 6]},
        {"chart": "box", "data": {"a": [1, 2, 3, 9], "b": [2, 3, 4]}, "unit": "", "points": True},
        {"chart": "strip", "data": {"a": [30, 31, 33], "b": [10, 12]}, "ci": True, "horizontal": True},
        {"chart": "ecdf", "data": {"a": [1, 2, 3], "b": [2, 3, 4]}, "ref": 2.5, "ref_label": "limit"},
        {"chart": "violin", "data": {"a": [1, 2, 3, 9], "b": [2, 3, 4]}, "unit": "", "scale": "width"},
        {"chart": "bars", "data": {"a": 2, "b": 3}, "runs": {"a": [1, 3], "b": [2, 4]}, "unit": ""},
        {"chart": "hbar", "data": {"a": [30, 12]}, "series": ["x", "y"], "runs": {"a": [[28, 32], [11, 13]]}},
        {"chart": "line", "series": {"a": [1, 2, 3]}, "x": [0, 1, 2], "runs": {"a": [[1, 2, 4], [1, 2, 2]]}},
    ]
    for s in specs:
        fig = vl.from_spec(json.loads(json.dumps(s)))
        assert fig.kind == s["chart"] and fig.svg() == vl.from_spec(s).svg()


def test_runs_on_bars_clear_the_labels():
    svg = vl.bars({"a": 30.0}, runs={"a": [20.0, 30.0, 50.0]}).svg()
    dots_y = [float(y) for y in re.findall(r'<circle cx="[\d.]+" cy="([\d.]+)"', svg)]
    assert len(dots_y) == 3
    label_y = float(re.search(r'<text x="[\d.]+" y="([\d.]+)"[^>]*text-anchor="middle"[^>]*>30%</text>', svg).group(1))
    assert label_y < min(dots_y) - 4  # the value label sits above the highest run
    svg = vl.hbar({"a": 30.0}, runs={"a": [20.0, 30.0, 50.0]}).svg()
    dots_x = [float(x) for x in re.findall(r'<circle cx="([\d.]+)"', svg)]
    label_x = float(re.search(r'<text x="([\d.]+)"[^>]*><tspan[^>]*>30%</tspan>', svg).group(1))
    assert label_x > max(dots_x) + 4  # past the outermost run
    svg = vl.line({"a": [1, 2], "b": [2, 1]}, runs={"b": [[2.1, 0.9], [1.9, 1.2], [2.0, 1.0]]}, unit="").svg()
    assert svg.count('stroke-opacity="0.4"') == 3


def test_runs_errors():
    with pytest.raises(ValueError, match="not in the data"):
        vl.bars({"a": 1}, runs={"b": [1, 2]})
    with pytest.raises(ValueError, match="one per series"):
        vl.bars({"a": [1, 2]}, series=["x", "y"], runs={"a": [1, 2, 3]})
    with pytest.raises(ValueError, match="entries"):
        vl.hbar({"a": 1, "b": 2}, runs=[[1, 2]])
    with pytest.raises(ValueError, match="not one of the series"):
        vl.line({"a": [1, 2]}, runs={"b": [[1, 2]]})


def test_swarm_keeps_dots_apart():
    pos = [10.0, 10.0, 10.5, 11.0, 30.0, 30.0, 12.0, 9.0]
    offs = dist.swarm(pos, 3.0)
    assert offs == dist.swarm(pos, 3.0)  # deterministic
    for i in range(len(pos)):
        for j in range(i):
            assert math.hypot(pos[i] - pos[j], offs[i] - offs[j]) >= 6.0 - 1e-6
    a, b = dist.swarm([5.0, 5.0], 3.0)
    assert a == -b != 0  # a pair of ties sits symmetrically on the center line
    assert max(abs(o) for o in dist.swarm([0.0] * 9, 3.0, limit=4.0)) <= 4.0 + 1e-9
    assert dist.swarm([1.0, 1.0], 3.0, limit=-2.0) == [0.0, 0.0]
    assert len(set(dist.swarm([float(i % 7) for i in range(500)], 1.0, limit=10.0))) > 1  # the large-n path


def test_tukey_and_quantiles():
    t = dist.tukey([1, 2, 3, 4, 5, 6, 7, 8, 9, 100])
    assert (t.q1, t.median, t.q3) == (3.25, 5.5, 7.75)  # numpy's default interpolation
    assert t.low == 1 and t.high == 9 and t.outliers == [100]
    assert dist.tukey([4.0]).median == 4.0
    assert dist.t975(1) == 12.706 and abs(dist.t975(31) - 2.0395) < 1e-3 and abs(dist.t975(1000) - 1.9623) < 1e-3
    lo, hi = dist.mean_ci([1.0, 2.0, 3.0])
    assert abs(lo - (2 - 4.303 / math.sqrt(3))) < 1e-9 and abs(hi - (2 + 4.303 / math.sqrt(3))) < 1e-9
    assert dist.mean_ci([1.0]) is None


def test_bins():
    vals = [0.5 * i for i in range(100)]  # 0 .. 49.5
    edges = dist.bin_edges(vals)
    w = edges[1] - edges[0]
    assert w in (5.0, 10.0) and edges[0] <= 0 and edges[-1] >= 49.5  # FD rounded to a nice width
    assert all(abs((e - edges[0]) / w - round((e - edges[0]) / w)) < 1e-9 for e in edges)
    assert sum(dist.bin_counts(vals, edges)) == 100
    assert dist.bin_edges(vals, 4) == [0.0, 12.375, 24.75, 37.125, 49.5]
    assert dist.bin_edges(vals, [10, 0, 20]) == [0.0, 10.0, 20.0]
    assert dist.bin_counts([0, 10, 20, 25], [0, 10, 20]) == [1, 2]  # the last bin includes its right edge
    whole = dist.bin_edges([1, 2, 2, 3, 3, 3, 7])
    assert whole[0] == 0.5 and whole[1] == 1.5  # one bar per whole number, centered on it
    assert dist.bin_edges([5, 5, 5]) == [4.5, 5.5]
    with pytest.raises(ValueError):
        dist.bin_edges(vals, [1])


def test_histogram_percent_and_domain():
    f = vl.histogram({"a": [1, 2, 3, 4], "b": [1, 1, 1, 9]}, stat="percent", bins=[0, 5, 10], domain=(0, 10),
                     legend=True)
    body = f.render(960)
    assert [lab for lab, _ in body.legend] == ["a", "b"]  # legend=True asks for a legend instead of labels
    assert vl.histogram({"a": [1, 2, 3], "b": [7, 8, 9]}).render(960).legend is None  # labeled directly
    with pytest.raises(ValueError):
        vl.histogram([1, 2], stat="density")


def test_box_and_strip_labels_sit_by_their_marks():
    svg = vl.box({"a": [1, 2, 3, 4, 5, 6, 7, 30]}, unit="").svg()
    assert ">4.5<" in svg  # the median, written beside the box
    svg = vl.strip({"a": [1.0, 2.0, 6.0]}, unit="", decimals=1).svg()
    assert ">3.0<" in svg  # the mean
    assert ">3.0<" not in vl.strip({"a": [1.0, 2.0, 6.0]}, unit="", decimals=1, values=False).svg()


def test_violin_density():
    from viz.charts.violin import GRID, density, silverman
    vals = [float(v) for v in range(-20, 21)]
    curve = density(vals, silverman(vals))
    assert len(curve) == GRID and curve[0][0] == -20 and curve[-1][0] == 20
    area = sum((b[0] - a[0]) * (a[1] + b[1]) / 2 for a, b in pairwise(curve))
    assert 0.8 < area < 1.0  # a density, minus what spills past the lowest and highest values
    big = [float(i % 101) for i in range(3000)]  # above 2,000 values the kernel runs over bins
    assert abs(sum(d for _, d in density(big, 5.0)) - sum(d for _, d in density(big[:2000], 5.0))) < 0.05
    assert silverman([3.0, 3.0, 3.0]) == 0
    with pytest.raises(ValueError):
        vl.violin({"a": [1, 2]}, scale="count")
    with pytest.raises(ValueError):
        vl.violin({"a": [1, 2]}, bandwidth=0)


def test_text_follows_the_house_rules():
    """Text in the new charts is at least 12 px (ticks use the tick size) and only in the three ink colors."""
    inks = {th.INK, th.INK2, th.MUTED}
    for name, f in examples().items():
        if not any(name.startswith(k) for k in NEW):
            continue
        body = f.render(960).svg
        for tag in re.findall(r"<(?:text|tspan)[^>]*>", body):
            size = float(re.search(r'font-size="([\d.]+)"', tag).group(1)) if "font-size" in tag else None
            if size is not None:
                assert size >= 12 or size == th.TICK_SIZE, (name, tag)
            m = re.search(r' fill="([^"]+)"', tag)
            if m:
                assert m.group(1) in inks, (name, tag)


def test_panels_align_vertical_charts():
    fig = vl.panels([vl.box({"A long group label that wraps": [1, 2, 3]}, unit=""), vl.strip({"B": [1.0, 2.0]})])
    assert fig.svg().startswith("<svg")


def test_panels_share_each_panels_own_legend():
    # a panel's own legend joins the shared one, each label once (#4: drawing it raised ModuleNotFoundError)
    a = vl.bars({"A": 1, "B": 2}, legend={"Control": "gray", "Treatment": "orange"})
    b = vl.bars({"A": 3, "B": 4}, legend=[("Treatment", "orange"), ("Search", "blue")])
    fig = vl.panels([a, b])
    svg = fig.svg()
    assert ">Control<" in svg and ">Treatment<" in svg and ">Search<" in svg
    assert fig.body(960).legend == [("Control", th.color("gray")), ("Treatment", th.color("orange")),
                                    ("Search", th.color("blue"))]
