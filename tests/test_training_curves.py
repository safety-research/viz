"""Training curves and trade-offs: smoothed lines, log y axes, marks at x values, stacked areas and Pareto frontiers.
Everything here composes SVG without a browser."""
from __future__ import annotations

import json
import math
import os
import random
import re
import subprocess
import sys

import pytest

import viz as vl
from viz import access, checks
from viz import text as T
from viz import theme as th
from viz.charts import axis as A
from viz.charts.area import _stack
from viz.charts.dist import seg_hits
from viz.charts.line import smoothed
from viz.charts.scatter import pareto


def reward(final: float, seed: int, n: int = 201) -> list[float]:
    """A made-up noisy RL reward curve rising from about 0.2 toward `final`, the same on every run."""
    rng = random.Random(seed)
    return [round(0.2 + (final - 0.2) * (1 - math.exp(-4 * k / n)) + rng.gauss(0, 0.09), 3) for k in range(n)]


RL_STEPS = list(range(0, 2001, 10))
STEPS = list(range(0, 2001, 100))
ACCURACY = [41, 41, 42, 42, 43, 43, 47, 51, 54, 57, 59, 61, 62, 63, 64, 65, 66, 66, 67, 67, 67]
LOSS = {  # (training compute in PF-days, validation loss), per model size
    "Small model": [(0.01, 4.42), (0.03, 3.98), (0.1, 3.66), (0.3, 3.45), (1, 3.33), (3, 3.27)],
    "Medium model": [(0.03, 4.25), (0.1, 3.72), (0.3, 3.31), (1, 3.02), (3, 2.85), (10, 2.76)],
    "Large model": [(0.1, 4.05), (0.3, 3.46), (1, 2.98), (3, 2.62), (10, 2.39), (30, 2.25), (100, 2.17)],
}
CHECKPOINTS = [0, 250, 500, 750, 1000, 1250, 1500, 1750]
SHARES = {"Answered": [52, 55, 61, 66, 70, 74, 77, 79], "Asked a question": [17, 18, 17, 16, 15, 14, 13, 13],
          "Refused": [31, 27, 22, 18, 15, 12, 10, 8]}
MODELS = {  # (dollars per million output tokens, accuracy %)
    "Model A": (15.0, 88), "Model B": (10.0, 84), "Model C": (8.0, 86), "Model D": (4.0, 81), "Model E": (3.0, 76),
    "Model F": (2.5, 79), "Model G": (1.2, 70), "Model H": (0.8, 72), "Model I": (0.6, 57), "Model J": (0.3, 58)}


def gallery() -> dict[str, vl.Figure]:
    """The proposed gallery figure for each feature: plain titles, no subtitles."""
    return {
        "smooth": vl.line(
            {"Without curriculum": reward(0.48, 3), "With curriculum": reward(0.74, 4)}, x=RL_STEPS, smooth=0.9,
            roles={"baseline": "Without curriculum", "intervention": "With curriculum"}, unit="", decimals=2,
            xlabel="RL step", ylabel="Mean reward", title="The curriculum raised final mean reward from 0.46 to 0.71"),
        "log": vl.line(
            LOSS, xscale="log", yscale="log", unit="", decimals=1, markers=False,
            roles={"ordered": ["Small model", "Medium model", "Large model"]},
            xlabel="Training compute (PF-days)", ylabel="Validation loss",
            title="Larger models reached lower loss once compute passed 1 PF-day"),
        "marks": vl.line(
            {"Held-out accuracy": ACCURACY}, x=STEPS, marks={500: "RL starts", 1500: "Checkpoint we chose"},
            decimals=0, markers=False, xlabel="Training step",
            title="Held-out accuracy rose from 43% to 67% after RL started"),
        "area": vl.area(
            SHARES, x=CHECKPOINTS, normalize=True, colors=["blue", "beige", "coral"], xlabel="Training step",
            ylabel="Share of answers", title="Refusals fell from 31% to 8% over eight checkpoints"),
        "frontier": vl.scatter(
            MODELS, frontier="upper-left", labels=True, yunit="%", yticks=[50, 60, 70, 80, 90],
            xlabel="Cost per million tokens ($)", ylabel="Accuracy",
            title="Six of ten models were on the cost-accuracy frontier"),
    }


def examples() -> dict[str, vl.Figure]:
    """One figure per feature and option, built fresh on every call."""
    runs = [reward(0.7, s, 41) for s in (11, 12, 13)]
    return {
        **gallery(),
        "smooth_runs": vl.line({"Reward": [sum(v) / 3 for v in zip(*runs)]}, x=list(range(0, 401, 10)),
                               runs={"Reward": runs}, smooth=0.8, unit=""),
        "smooth_gaps": vl.line({"a": [1.0, None, 3.0, float("nan"), 2.0, 4.0]}, smooth=0.6, unit="", markers=True),
        "log_exponents": vl.line({"Loss": [(1e18, 4.2), (1e19, 3.1), (1e20, 2.6), (1e21, 2.3), (1e22, 2.1)]},
                                 xscale="log", yscale="log", unit=""),
        "log_wide": vl.line({"Error": [0.002, 0.03, 0.4, 5.0]}, yscale="log", unit="", ref=1, ref_label="chance"),
        "log_tiny": vl.line({"Learning rate": [1e-6, 3e-6, 1e-5, 1e-4]}, yscale="log", unit="", ylabel="LR"),
        "log_domain": vl.line({"a": [3.0, 4.0, 5.0]}, yscale="log", domain=(1, 1000), unit="",
                              bands={"a": ([2.5, 3.5, 4.5], [3.5, 4.5, 5.5])}),
        "log_ticks": vl.line({"a": [3.0, 4.0, 5.0]}, yscale="log", ticks=[2, 3, 4, 5, 6], unit=""),
        "marks_category": vl.line({"a": [31, 26, 21, 17]}, x=[0, 1e6, 3e6, 1e7], xscale="category",
                                  xtick_labels={0: "0", 1e6: "1M", 3e6: "3M", 1e7: "10M"}, marks={3e6: "Dose we used"}),
        "marks_log": vl.line(LOSS, xscale="log", marks={1: "Our budget"}, unit=""),
        "marks_crowded": vl.line({"a": [1, 2, 3]}, x=[0, 1, 2], unit="",
                                 marks={0.9: "First long label here", 1.0: "Second long label here", 1.1: "Third",
                                        2: "End", 0: None}),
        "area_counts": vl.area({"Answered": [120, 150, 170, 180], "Refused": [80, 40, 20, 10]}, x=[0, 1, 2, 3],
                               unit="", ylabel="Answers", xlabel="Checkpoint", ticks=[0, 100, 200]),
        "area_category": vl.area(SHARES, x=list(range(1, 9)), xscale="category", normalize=True,
                                 xtick_labels={k: f"C{k}" for k in range(1, 9)}, marks={4: "RL starts"}),
        "area_log": vl.area({"a": [1, 2, 3], "b": [3, 2, 1]}, x=[1e3, 1e4, 1e5], xscale="log", unit="",
                            domain=(0, 5), height=240),
        "area_thin": vl.area({"Big": [90, 95, 97, 99], "Thin": [10, 5, 3, 1]}, normalize=True),
        "area_legend": vl.area({"a": [1, 2], "b": [2, 1]}, unit="", legend=True, end_labels=False, xticks=[0, 1]),
        "frontier_groups": vl.scatter({"g1": [(1, 2), (2, 3)], "g2": [(3, 1), (2, 2)]}, frontier="upper-right"),
    }


# ---------------------------------------------------------------------------------------------------- helpers

def attrs(tag: str) -> dict[str, str]:
    return dict(re.findall(r'([\w:-]+)="([^"]*)"', tag))


def elements(svg: str, name: str) -> list[dict[str, str]]:
    return [attrs(t) for t in re.findall(rf"<{name}\b[^>]*>", svg)]


def texts(svg: str) -> list[tuple[dict[str, str], str]]:
    """Every plain <text> (no tspans) with its attributes and words."""
    return [(attrs(a), s) for a, s in re.findall(r"<text\b([^>]*)>([^<]*)</text>", svg)]


def points(poly: dict[str, str]) -> list[tuple[float, float]]:
    return [tuple(float(v) for v in p.split(",")) for p in poly["points"].split()]


def path_points(d: str) -> list[tuple[float, float]]:
    return [(float(a), float(b)) for a, b in re.findall(r"(-?[\d.]+),(-?[\d.]+)", d)]


def x_ticks(svg: str) -> list[str]:
    return [s for a, s in texts(svg) if a.get("text-anchor") == "middle" and a["font-size"] == "12"
            and a["fill"] == th.MUTED]


def y_ticks(svg: str) -> list[str]:
    return [s for a, s in texts(svg) if a.get("text-anchor") == "end" and a["font-size"] == "12"
            and a["fill"] == th.MUTED]


def gridlines(svg: str) -> list[float]:
    """The y of each horizontal gridline, top first."""
    return sorted(float(e["y1"]) for e in elements(svg, "line") if e["y1"] == e["y2"] and e["x1"] != e["x2"])


def mark_lines(svg: str) -> list[dict[str, str]]:
    return [e for e in elements(svg, "line") if e["x1"] == e["x2"] and e.get("stroke-dasharray") == "4 4"]


@pytest.fixture(autouse=True)
def fresh():
    checks.reset()
    vl.set_roles()
    yield
    vl.set_defaults(theme="light")
    vl.set_roles()
    checks.reset()


# ---------------------------------------------------------------------------------------------------- every figure

@pytest.mark.parametrize("name", list(examples()))
def test_renders_clean_svg(name):
    svg = examples()[name].svg()
    assert svg.startswith("<svg") and svg.endswith("</svg>")
    for bad in ("NaN", "nan", "None", "inf"):
        assert bad not in re.sub(r">[^<]*<", "><", svg), bad  # no broken numbers in any attribute


@pytest.mark.parametrize("name", list(examples()))
def test_deterministic(name):
    a, b = examples()[name], examples()[name]
    assert a.svg() == b.svg() == a.svg()


def test_deterministic_across_processes():
    here = os.path.dirname(__file__)
    code = (f"import hashlib, sys; sys.path.insert(0, {here!r}); from test_training_curves import examples; "
            "print(hashlib.sha256(''.join(f.svg() for f in examples().values()).encode()).hexdigest())")
    digests = set()
    for seed in ("1", "2"):
        env = dict(os.environ, PYTHONHASHSEED=seed)
        digests.add(subprocess.run([sys.executable, "-c", code], env=env, capture_output=True, text=True,
                                   check=True).stdout.strip())
    (digest,) = digests
    assert re.fullmatch(r"[0-9a-f]{64}", digest)


def test_area_is_registered():
    assert "area" in vl.CHARTS and "area" in vl.__all__ and vl.CHARTS["area"] is vl.area


@pytest.mark.parametrize("name", list(gallery()))
def test_plain_titles_pass_the_checks(name):
    assert gallery()[name].check() == []


@pytest.mark.parametrize("name", list(examples()))
def test_text_sizes(name):
    """Nothing under 12 px but a power of ten's raised exponent, which the log x axis already writes that way."""
    body = examples()[name].render(960).svg
    for tag in re.findall(r"<(?:text|tspan)\b[^>]*>", body):
        m = re.search(r'font-size="([\d.]+)"', tag)
        if m and float(m.group(1)) < th.MIN_TEXT:
            assert float(m.group(1)) == pytest.approx(th.TICK_SIZE * A.EXP) and 'dy="-' in tag, tag


def test_dark_theme_reads_its_tokens_at_render():
    vl.set_defaults(theme="dark")
    light = {th._LIGHT[k] for k in ("GRID", "AXIS", "MUTED", "INK2")}
    for name, f in examples().items():
        svg = f.svg()
        assert th.BG in svg, name
        assert not light & set(re.findall(r'"(#[0-9A-F]{6})"', svg)), name
    area = examples()["area"].render(960).svg
    assert any(p.get("stroke") == th.BG for p in elements(area, "path"))  # the lines between bands
    front = examples()["frontier"].render(960).svg
    assert any(p.get("stroke") == th.INK2 and p.get("stroke-width") == "1.5" for p in elements(front, "path"))
    for name in gallery():
        assert gallery()[name].check() == [], name


def test_json_specs_round_trip():
    specs = [
        {"chart": "line", "series": {"a": [1.0, 3.0, 2.0, 4.0]}, "x": [0, 500, 1000, 1500], "smooth": 0.6,
         "marks": {"500": "RL starts"}, "unit": ""},
        {"chart": "line", "series": {"a": [[1, 4.2], [10, 3.1], [100, 2.6]]}, "xscale": "log", "yscale": "log",
         "unit": ""},
        {"chart": "area", "series": {"a": [1, 2], "b": [2, 1]}, "x": [0, 1], "normalize": True, "marks": {"1": "x"}},
        {"chart": "scatter", "points": {"a": [1, 2], "b": [2, 3], "c": [3, 1]}, "frontier": "upper-left",
         "labels": True},
    ]
    for s in specs:
        fig = vl.from_spec(json.loads(json.dumps(s)))
        assert fig.kind == s["chart"] and fig.svg() == vl.from_spec(s).svg()
    with_int_keys = vl.line({"a": [1.0, 3.0, 2.0, 4.0]}, x=[0, 500, 1000, 1500], smooth=0.6, marks={500: "RL starts"},
                            unit="")
    assert vl.from_spec(json.loads(json.dumps(specs[0]))).svg() == with_int_keys.svg()


# ---------------------------------------------------------------------------------------------------- smoothing

def test_smoothing_is_tensorboards_debiased_moving_average():
    # by hand with weight 0.5: the running average is 0.5, 1.25, 2.125, divided by 1 - 0.5^n
    got = [y for _, y in smoothed([(0, 1.0), (1, 2.0), (2, 3.0)], 0.5)]
    assert got == pytest.approx([0.5 / 0.5, 1.25 / 0.75, 2.125 / 0.875])
    for w in (0.0, 0.3, 0.9, 0.99):
        assert smoothed([(0, 7.0), (1, 1.0)], w)[0][1] == pytest.approx(7.0)  # debiased: starts at the first value
    assert smoothed([(0, 1.0), (1, 5.0), (2, 2.0)], 0.0) == [(0, 1.0), (1, 5.0), (2, 2.0)]  # weight 0: unchanged
    assert smoothed([(0, 2.0), (1, 2.0), (2, 2.0)], 0.9) == [(0, 2.0), (1, 2.0), (2, 2.0)]  # constant: unchanged
    gaps = smoothed([(0, 1.0), (1, None), (2, 3.0)], 0.5)  # a missing value stays missing and doesn't count
    assert gaps[1] == (1, None) and gaps[2][1] == pytest.approx((0.5 * 0.5 + 0.5 * 3.0) / 0.75)


def test_smoothed_line_draws_raw_faint_and_smoothed_bold():
    f = vl.line({"a": [1, 2, 3]}, x=[0, 1, 2], smooth=0.5, unit="", decimals=2)
    svg = f.render(960).svg
    faint = [p for p in elements(svg, "path") if p.get("stroke-opacity") == "0.4"]
    bold = [p for p in elements(svg, "path") if p.get("stroke-width") == "2.25"]
    assert len(faint) == 1 and len(bold) == 1
    assert len(path_points(faint[0]["d"])) == len(path_points(bold[0]["d"])) == 3
    assert path_points(faint[0]["d"])[-1][1] < path_points(bold[0]["d"])[-1][1]  # the raw 3 sits above the smoothed
    assert ">2.43<" in svg and ">3.00<" not in svg  # the end value is the smoothed one
    assert "<circle" not in svg  # markers are off by default when smoothing
    assert vl.line({"a": [1, 2, 3]}, smooth=0.5, unit="", markers=True).svg().count("<circle") == 3
    assert vl.line({"a": [1, 2, 3]}, unit="").svg().count("<circle") == 3  # without smoothing they stay on


def test_smoothing_keeps_the_raw_values_on_the_axis():
    ys = [1.0] * 20 + [10.0] + [1.0] * 20
    svg = vl.line({"a": ys}, smooth=0.95, unit="").render(960).svg
    assert max(float(t.replace(",", "")) for t in y_ticks(svg)) >= 10  # the spike isn't clipped
    top = gridlines(svg)[0]
    assert all(y >= top - 0.01 for p in elements(svg, "path") for _, y in path_points(p["d"]))


def test_smoothing_with_runs_keeps_the_raw_runs_faint():
    svg = examples()["smooth_runs"].render(960).svg
    assert len([p for p in elements(svg, "path") if p.get("stroke-opacity") == "0.4"]) == 3  # the runs, no extra line


def test_smooth_errors():
    for bad in (1, 1.0, -0.1, True, "0.9", float("nan")):
        with pytest.raises(ValueError, match="smooth"):
            vl.line({"a": [1, 2]}, smooth=bad)


def test_many_x_values_tick_at_round_steps():
    assert x_ticks(vl.line({"a": list(range(201))}, x=RL_STEPS, unit="").svg()) == ["0", "500", "1,000", "1,500",
                                                                                     "2,000"]
    assert x_ticks(vl.line({"a": list(range(13))}, unit="").svg()) == ["0", "2", "4", "6", "8", "10", "12"]
    assert x_ticks(vl.line({"a": [1, 2, 3]}, x=[0, 5, 7], unit="").svg()) == ["0", "5", "7"]  # few: every value
    named = vl.line({"a": list(range(20))}, xtick_labels={0: "start", 19: "end"}, unit="").svg()
    assert x_ticks(named) == ["start", "end"]


# ---------------------------------------------------------------------------------------------------- log y axis

@pytest.mark.parametrize("values, want", [
    ((2.05, 4.4), (2, 5, [2, 3, 4, 5])),               # a loss: 1-9 steps
    ((1.1, 9.5), (1, 10, [1, 2, 5, 10])),              # one decade: 1-2-5
    ((0.6, 3), (0.5, 5, [0.5, 1, 2, 5])),
    ((2, 80), (1, 100, [1, 10, 100])),                 # powers of ten
    ((1e18, 3e22), (1e18, 1e23, [1e18, 1e19, 1e20, 1e21, 1e22, 1e23])),
    ((2e20, 5e20), (1e20, 1e21, [1e20, 1e21])),       # outside 0.001..1,000 the ticks stay powers of ten
    ((2, 2), (2, 3, [2, 3])),
])
def test_log_ticks(values, want):
    lo, hi, tk = A.log_ticks(*values)
    assert (lo, hi) == pytest.approx(want[:2]) and tk == pytest.approx(want[2])


def test_log_axis_takes_ticks_and_domains():
    assert A.log_axis([3, 4], domain=(1, 1000)) == (1, 1000, [1, 10, 100, 1000])
    assert A.log_axis([3, 4], ticks=[2, 3, 4]) == (2, 4, [2, 3, 4])
    assert A.log_axis([3, 4], domain=(None, 100)) == (1, 100, [1, 10, 100])  # the free end snaps to a power of ten
    for kw in ({"ticks": [0, 1]}, {"domain": (0, 10)}, {"domain": (10, 1)}):
        with pytest.raises(ValueError, match="log"):
            A.log_axis([3, 4], **kw)


def test_log_y_spaces_powers_of_ten_evenly():
    svg = vl.line({"a": [1, 10, 100]}, x=[0, 1, 2], yscale="log", unit="").render(960).svg
    ys = [float(c["cy"]) for c in elements(svg, "circle")]
    assert ys[0] - ys[1] == pytest.approx(ys[1] - ys[2], abs=0.02)
    assert y_ticks(svg) == ["1", "10", "100"]


def test_log_y_writes_powers_outside_a_thousandth_to_a_thousand_with_an_exponent():
    svg = examples()["log_tiny"].render(960).svg
    for k in ("−6", "−5", "−4"):
        assert re.search(rf'font-size="{th.TICK_SIZE * A.EXP:g}"[^>]*>{k}</tspan>', svg), k
    assert y_ticks(examples()["log_wide"].svg()) == ["0.001", "0.01", "0.1", "1", "10"]
    assert y_ticks(examples()["smooth"].svg()) != []  # linear axes keep their own labels
    svg = examples()["log_exponents"].render(960).svg
    assert y_ticks(svg) == ["2", "3", "4", "5"] and ">20</tspan>" in svg  # 10^20 on the x axis


def test_log_x_ticks_take_only_the_decimals_they_need():
    svg = vl.line({"a": [1, 2, 3, 4, 5]}, x=[0.01, 0.1, 1, 10, 100], xscale="log", unit="").svg()
    assert x_ticks(svg) == ["0.01", "0.1", "1", "10", "100"]


def test_log_y_errors():
    with pytest.raises(ValueError, match="above 0"):
        vl.line({"a": [1, 0, 2]}, yscale="log")
    with pytest.raises(ValueError, match="above 0"):
        vl.line({"a": [1, 2]}, yscale="log", bands={"a": ([-1, 1], [2, 3])})
    with pytest.raises(ValueError, match="above 0"):
        vl.line({"a": [1, 2]}, yscale="log", runs={"a": [[1, -2]]})
    with pytest.raises(ValueError, match="above 0"):
        vl.line({"a": [1, 2]}, yscale="log", ref=0)
    with pytest.raises(ValueError, match="yscale"):
        vl.line({"a": [1, 2]}, yscale="sqrt")
    with pytest.raises(ValueError, match="xscale"):
        vl.line({"a": [1, 2]}, xscale="time")
    assert vl.line({"a": [1, None, 2]}, yscale="log", unit="").svg().startswith("<svg")  # missing values are fine


# ---------------------------------------------------------------------------------------------------- marks

def test_marks_draw_dashed_lines_with_labels_above_the_plot():
    svg = examples()["marks"].render(960).svg
    lines = mark_lines(svg)
    assert len(lines) == 2
    top, bottom = gridlines(svg)[0], gridlines(svg)[-1]
    axis = next(e for e in elements(svg, "line") if e["y1"] == e["y2"] and float(e["y1"]) == bottom)
    left, right = float(axis["x1"]), float(axis["x2"])
    for e, frac in zip(lines, (0.25, 0.75)):  # 500 and 1,500 of 0..2,000
        assert float(e["x1"]) == pytest.approx(left + frac * (right - left), abs=0.02)
        assert float(e["y1"]) == pytest.approx(top) and float(e["y2"]) == pytest.approx(bottom)
    labels = {s: a for a, s in texts(svg) if s in ("RL starts", "Checkpoint we chose")}
    assert len(labels) == 2
    for (s, a), e in zip(sorted(labels.items(), key=lambda kv: float(kv[1]["x"])), lines):
        assert float(a["y"]) < top and a["fill"] == th.MUTED and float(a["font-size"]) == th.MIN_TEXT
        middle = float(a["x"]) + T.width(s, th.MIN_TEXT) / 2
        assert middle == pytest.approx(float(e["x1"]), abs=0.05)  # centered over its line


def test_mark_labels_stay_inside_the_figure_and_apart():
    W = 960
    svg = examples()["marks_crowded"].render(W).svg
    names = {"First long label here", "Second long label here", "Third", "End"}
    boxes = [(float(a["x"]), float(a["y"]), float(a["x"]) + T.width(s, th.MIN_TEXT)) for a, s in texts(svg) if s in names]
    assert len(boxes) == 4 and len(mark_lines(svg)) == 5  # an unlabeled mark draws its line alone
    for x0, _, x1 in boxes:
        assert 0 <= x0 and x1 <= W
    for i, (a0, ay, a1) in enumerate(boxes):
        for b0, by, b1 in boxes[i + 1:]:
            assert ay != by or a1 + A.MARK_GAP <= b0 + 1e-6 or b1 + A.MARK_GAP <= a0 + 1e-6
    assert len({y for _, y, _ in boxes}) >= 2  # the crowded labels stack in rows
    assert gridlines(svg)[0] > gridlines(examples()["marks"].render(W).svg)[0]  # rows push the plot down


def test_mark_layout_pushes_close_labels_apart_in_one_row():
    X = lambda v: 100 + 400 * v
    layout, rows = A.mark_layout([(0.5, "RL starts"), (0.6, "Checkpoint we chose")], X, 0, 960)
    assert rows == 1
    (a0, la, _), (b0, lb, _) = layout
    assert a0 + T.width(la, th.MIN_TEXT) + A.MARK_GAP <= b0 + 1e-6
    assert b0 <= X(0.6) <= b0 + T.width(lb, th.MIN_TEXT)  # still over its own line
    assert A.mark_layout([(0.5, "")], X, 0, 960) == ([], 0)


def test_marks_work_with_every_xscale():
    cat = examples()["marks_category"].render(960).svg
    (line,) = mark_lines(cat)
    ticks = {s: float(a["x"]) for a, s in texts(cat) if s in ("0", "1M", "3M", "10M")}
    assert float(line["x1"]) == pytest.approx(ticks["3M"])
    log = examples()["marks_log"].render(960).svg
    (line,) = mark_lines(log)
    ticks = {s: float(a["x"]) for a, s in texts(log) if a.get("text-anchor") == "middle"}  # the x ticks
    assert float(line["x1"]) == pytest.approx(ticks["1"])
    with pytest.raises(ValueError, match="category"):
        vl.line({"a": [1, 2]}, x=[0, 1], xscale="category", marks={0.5: "between"})
    with pytest.raises(ValueError, match="above 0"):
        vl.line({"a": [1, 2]}, x=[1, 10], xscale="log", marks={0: "zero"})
    with pytest.raises(TypeError):
        vl.line({"a": [1, 2]}, marks=[500])
    with pytest.raises(ValueError, match="x value"):
        vl.line({"a": [1, 2]}, marks={"start": "RL starts"})


def test_marks_past_the_data_widen_the_x_axis():
    svg = vl.line({"a": [1, 2, 3]}, x=[0, 500, 1000], marks={1500: "Later"}, unit="").render(960).svg
    (line,) = mark_lines(svg)
    bold = next(p for p in elements(svg, "path") if p.get("stroke-width") == "2.25")
    assert path_points(bold["d"])[-1][0] < float(line["x1"])  # the line ends before the mark
    right = max(float(e["x2"]) for e in elements(svg, "line") if e["y1"] == e["y2"])
    assert float(line["x1"]) == pytest.approx(right)  # the mark is the plot's right edge


# ---------------------------------------------------------------------------------------------------- area

def test_stack_orders_x_counts_missing_as_zero_and_normalizes():
    names, xs, vals = _stack({"a": [1, 3], "b": [1, 1]}, x=[1, 0], normalize=True)
    assert names == ["a", "b"] and xs == [0, 1] and vals == [[75, 50], [25, 50]]
    _, _, vals = _stack({"a": [1, None, float("nan")], "b": [1, 1, 0]})
    assert vals == [[1, 0, 0], [1, 1, 0]]
    _, _, vals = _stack({"a": [0, 2], "b": [0, 2]}, normalize=True)
    assert vals == [[0, 50], [0, 50]]  # an x with nothing to share stays at 0


def test_area_stacks_the_first_series_at_the_bottom():
    svg = examples()["area"].render(960).svg
    polys = elements(svg, "polygon")
    assert [p["fill"] for p in polys] == [th.color("blue"), th.color("beige"), th.color("coral")]
    top, bottom = gridlines(svg)[0], gridlines(svg)[-1]
    assert max(y for _, y in points(polys[0])) == pytest.approx(bottom)  # the first band sits on the axis
    assert min(y for _, y in points(polys[-1])) == pytest.approx(top)  # shares fill the plot to 100%
    assert y_ticks(svg) == ["0%", "25%", "50%", "75%", "100%"]
    between = [p for p in elements(svg, "path") if p.get("stroke") == th.BG]
    assert len(between) == 2 and all(p["stroke-width"] == "1" for p in between)


def test_area_names_each_band_inside_or_beside_it():
    svg = examples()["area"].render(960).svg
    polys = elements(svg, "polygon")
    labels = {s: a for a, s in texts(svg) if s in SHARES}
    for name, poly in zip(SHARES, polys):  # all three fit inside their bands, in text that reads on the fill
        assert labels[name]["text-anchor"] == "end" and labels[name]["font-weight"] == "600"
        assert access.contrast(labels[name]["fill"], poly["fill"]) >= 4.5
    thin = examples()["area_thin"].render(960).svg
    polys = elements(thin, "polygon")
    labels = {s: a for a, s in texts(thin) if s in ("Big", "Thin")}
    assert labels["Big"]["text-anchor"] == "end" and access.contrast(labels["Big"]["fill"], polys[0]["fill"]) >= 4.5
    assert "text-anchor" not in labels["Thin"]  # beside the band, past the plot's right edge
    assert float(labels["Thin"]["x"]) > max(x for p in polys for x, _ in points(p))
    assert labels["Thin"]["fill"] == th.readable(polys[1]["fill"])
    assert access.contrast(labels["Thin"]["fill"], th.BG) >= 4.5
    assert float(labels["Thin"]["x"]) + T.width("Thin", 12.5, "sans", 600) <= 960
    assert vl.area({"a": [1, 2]}, unit="").svg().count(">a<") == 1  # named once, with no legend


def test_area_beside_names_stay_apart():
    svg = vl.area({"Big": [96, 97, 98], "Thin one": [2, 2, 1], "Thin two": [2, 1, 1]}, normalize=True).render(960).svg
    ys = sorted(float(a["y"]) for a, s in texts(svg) if s in ("Thin one", "Thin two"))
    assert len(ys) == 2 and ys[1] - ys[0] >= 15


def test_area_colors_follow_the_roles():
    f = vl.area(SHARES, x=CHECKPOINTS, normalize=True, roles={"control": "Answered", "intervention": "Refused"})
    fills = [p["fill"] for p in elements(f.body(960).svg, "polygon")]  # body() draws with the figure's roles
    assert fills[0] == th.color("gray") and fills[2] == th.color("coral")
    f.title = "Refusals fell from 31% to 8% over eight checkpoints"
    assert f.check() == []  # the control and a muted band may share gray: neither is an accent
    default = [p["fill"] for p in elements(vl.area(SHARES, normalize=True).body(960).svg, "polygon")]
    assert default == [th.color(c) for c in th.SERIES[:3]]
    vl.set_roles(intervention="Refused")  # roles set for the whole script apply too
    assert elements(vl.area(SHARES, normalize=True).body(960).svg, "polygon")[2]["fill"] == th.color("coral")


def test_area_options():
    counts = examples()["area_counts"].render(960)
    assert y_ticks(counts.svg) == ["0", "100", "200"] and "Answers" in counts.svg and "Checkpoint" in counts.svg
    cat = examples()["area_category"].render(960).svg
    assert x_ticks(cat) == [f"C{k}" for k in range(1, 9)] and len(mark_lines(cat)) == 1
    (mark,) = mark_lines(cat)
    assert mark["stroke"] == th.INK2  # over the bands, which cover the plot
    log = examples()["area_log"]
    body = log.render(960)
    assert body.height == 240 and y_ticks(body.svg)[-1] == "5"
    xs = sorted({x for p in elements(body.svg, "polygon") for x, _ in points(p)})
    assert xs[1] - xs[0] == pytest.approx(xs[2] - xs[1], abs=0.02)  # 10^3, 10^4, 10^5 evenly spaced
    legend = examples()["area_legend"]
    assert [lab for lab, _ in legend.render(960).legend] == ["a", "b"] and ">a<" in legend.svg()
    assert not [a for a, s in texts(legend.render(960).svg) if s in ("a", "b")]  # end_labels=False


def test_area_errors():
    with pytest.raises(ValueError, match="share one x"):
        vl.area({"a": [(0, 1), (1, 2)], "b": [(0, 1), (2, 2)]})
    with pytest.raises(ValueError, match="below 0"):
        vl.area({"a": [1, -2]})
    with pytest.raises(ValueError, match="at least one"):
        vl.area({})
    with pytest.raises(ValueError, match="xscale"):
        vl.area({"a": [1, 2]}, xscale="time")
    with pytest.raises(ValueError, match="above 0"):
        vl.area({"a": [1, 2]}, x=[0, 1], xscale="log")
    with pytest.raises(ValueError, match="category"):
        vl.area({"a": [1, 2]}, xscale="category", marks={0.5: "between"})


# ---------------------------------------------------------------------------------------------------- frontier

PTS = [("a", 1.0, 1.0), ("b", 2.0, 3.0), ("c", 3.0, 2.0), ("d", 0.5, 0.5), ("e", 2.0, 3.0)]


@pytest.mark.parametrize("corner, want", [
    ("upper-left", ["d", "a", "b", "e"]),   # cheaper and better: a tie with a frontier point is on it too
    ("upper-right", ["b", "e", "c"]),
    ("lower-left", ["d"]),
    ("lower-right", ["d", "a", "c"]),
])
def test_pareto_frontier_for_each_corner(corner, want):
    assert [PTS[i][0] for i in pareto(PTS, corner)] == want


def test_frontier_runs_under_the_points_through_the_frontier_in_x_order():
    svg = examples()["frontier"].render(960).svg
    line = next(p for p in elements(svg, "path") if p.get("stroke") == th.INK2)
    assert line["stroke-width"] == "1.5" and line["fill"] == "none"
    assert svg.index(line["d"]) < svg.index("<circle")  # drawn before the points
    xy = path_points(line["d"])
    assert len(xy) == 6 and [x for x, _ in xy] == sorted(x for x, _ in xy)
    dots = {(round(float(c["cx"]), 2), round(float(c["cy"]), 2)) for c in elements(svg, "circle")}
    assert all((round(x, 2), round(y, 2)) in dots for x, y in xy)


def test_frontier_bolds_the_labels_of_its_points_and_keeps_them_off_the_line():
    svg = examples()["frontier"].render(960).svg
    on = {"Model A", "Model C", "Model D", "Model F", "Model H", "Model J"}
    labels = {s: a for a, s in texts(svg) if s in MODELS}
    assert {s for s, a in labels.items() if a.get("font-weight") == "600"} == on
    assert all(labels[s]["fill"] == th.INK for s in on)
    line = next(p for p in elements(svg, "path") if p.get("stroke") == th.INK2)
    xy = path_points(line["d"])
    segs = [(*a, *b) for a, b in zip(xy, xy[1:])]
    for s, a in labels.items():
        w = T.width(s, 12, "sans", 600 if s in on else 400)
        x, y = float(a["x"]), float(a["y"])
        x0 = {"end": x - w, "middle": x - w / 2}.get(a.get("text-anchor"), x)
        assert not any(seg_hits(g, (x0, y - 11, x0 + w, y + 3)) for g in segs), s


def test_frontier_options_and_errors():
    plain = vl.scatter(MODELS, labels=True).render(960).svg
    assert not any(p.get("stroke") == th.INK2 for p in elements(plain, "path"))
    assert 'font-weight="600"' not in plain
    groups = examples()["frontier_groups"].render(960).svg
    assert len(path_points(next(p for p in elements(groups, "path") if p.get("stroke") == th.INK2)["d"])) == 2
    one = vl.scatter({"a": (1, 1), "b": (0, 0)}, frontier="upper-right", labels=True).render(960).svg
    assert not any(p.get("stroke") == th.INK2 for p in elements(one, "path"))  # one point: no line to draw
    with pytest.raises(ValueError, match="frontier"):
        vl.scatter(MODELS, frontier="top")


# ---------------------------------------------------------------------------------------------------- alt text

def test_alt_text_describes_the_new_options():
    alt = {k: f.alt_text() for k, f in gallery().items()}
    assert ("Line chart over RL step, smoothed with an exponential moving average (weight 0.9) over the faint raw "
            "values. Without curriculum: from 0.21 at 0 to 0.46 at 2000; With curriculum: from 0.20 at 0 to 0.71 "
            "at 2000.") in alt["smooth"]
    assert "Line chart over training compute (PF-days), on log-log axes. Small model: 4.4 at 0.01" in alt["log"]
    assert alt["marks"].endswith("Marked: RL starts at 500, Checkpoint we chose at 1500.")
    assert ("Stacked area chart over training step, each x as shares of its total, bands from the bottom up. "
            "Answered: 52% at 0, 55% at 250") in alt["area"]
    assert "Refused: 31% at 0, 27% at 250, 22% at 500" in alt["area"]
    assert alt["frontier"].endswith("Pareto frontier, where higher y and lower x are better: Model J, Model H, "
                                    "Model F, Model D, Model C, Model A.")
    assert "on a log y axis" in examples()["log_tiny"].alt_text()
    assert "Marked: Dose we used at 3M." in examples()["marks_category"].alt_text()
    assert "a line at 0" in examples()["marks_crowded"].alt_text()
    assert "Stacked area chart over checkpoint, bands from the bottom up. Answered: 120 at 0" in \
        examples()["area_counts"].alt_text()
    groups = examples()["frontier_groups"].alt_text()
    assert groups.endswith("Pareto frontier, where higher y and higher x are better: (2, 3), (3, 1).")
