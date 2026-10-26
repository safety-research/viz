"""Missing values in line charts (issue #2): a line breaks at a missing value, and a value with no present neighbor
stays visible. Everything here composes SVG without a browser."""
from __future__ import annotations

import math
import re

import pytest

import viz as vl
from viz.charts.line import segments, smoothed


def elements(svg: str, name: str) -> list[dict]:
    return [dict(re.findall(r'([\w:-]+)="([^"]*)"', t)) for t in re.findall(rf"<{name}\b[^>]*>", svg)]


def points(d: str) -> list[tuple[float, float]]:
    return [(float(a), float(b)) for a, b in re.findall(r"(-?[\d.]+),(-?[\d.]+)", d)]


def body(fig) -> str:
    return fig.body(960).svg


def bold(svg: str) -> list[list[tuple[float, float]]]:
    return [points(p["d"]) for p in elements(svg, "path") if p.get("stroke-width") == "2.25"]


def faint(svg: str) -> list[list[tuple[float, float]]]:
    return [points(p["d"]) for p in elements(svg, "path") if p.get("stroke-opacity") == "0.4"]


def markers(svg: str) -> list[tuple[float, float]]:
    return [(float(c["cx"]), float(c["cy"])) for c in elements(svg, "circle") if c.get("r") == "3.6"]


def run_dots(svg: str) -> list[dict]:
    return [c for c in elements(svg, "circle") if c.get("r") == "2.6"]


def test_segments_split_at_missing_values():
    assert segments([(0, 1), (1, None), (2, 3), (3, 4)]) == [[(0, 1)], [(2, 3), (3, 4)]]
    assert segments([(0, 1), (1, 2)]) == [[(0, 1), (1, 2)]]
    assert segments([(0, None)]) == [] and segments([]) == []


@pytest.mark.parametrize("gap", [None, math.nan])
def test_a_missing_value_breaks_the_bold_line_with_markers_on_or_off(gap):
    svg = body(vl.line({"a": [1, 2, gap, 4, 5]}, unit=""))
    lines, dots = bold(svg), markers(svg)
    assert len(lines) == 2 and lines[0] == dots[:2] and lines[1] == dots[2:]
    off = body(vl.line({"a": [1, 2, gap, 4, 5]}, unit="", markers=False))
    assert bold(off) == lines and markers(off) == []


def test_a_run_breaks_at_missing_values_and_a_lone_run_value_is_a_faint_dot():
    runs = [[1.2, 2.2, None, 4.2, None], {2: 3.3}]  # 4.2 sits between two missing steps; the second run has one value
    svg = body(vl.line({"a": [1, 2, 3, 4, 5]}, runs={"a": runs}, unit=""))
    xs = [x for x, _ in markers(svg)]
    assert [[x for x, _ in p] for p in faint(svg)] == [xs[:2]]  # nothing crosses the missing x
    dots = run_dots(svg)
    assert sorted(float(c["cx"]) for c in dots) == [xs[2], xs[3]]
    color = elements(svg, "path")[-1]["stroke"]
    assert all(c["fill"] == color and c["fill-opacity"] == "0.55" for c in dots)


def test_a_bold_value_with_no_present_neighbor_keeps_its_marker():
    ys = [1, None, 3, None, 5, 6]
    svg = body(vl.line({"a": ys}, unit="", markers=False))
    assert len(markers(svg)) == 2 and [len(p) for p in bold(svg)] == [2]
    assert len(markers(body(vl.line({"a": ys}, unit="")))) == 4  # markers on: each value once, the lone ones too
    one = body(vl.line({"a": [None, 42, None]}, unit="", markers=False))
    assert bold(one) == [] and len(markers(one)) == 1


def test_the_end_label_gives_the_last_present_value_at_its_height():
    svg = body(vl.line({"a": [1, 2, 3, None]}, unit=""))
    m = re.search(r'<text x="[\d.]+" y="([\d.]+)"[^>]*><tspan[^>]*>a</tspan><tspan[^>]*>3</tspan>', svg)
    assert m and float(m.group(1)) == pytest.approx(markers(svg)[-1][1] + 4.5, abs=0.01)


def test_with_smoothing_a_gap_breaks_the_smoothed_and_the_raw_line():
    ys = [1, 2, 3, None, 5, 6, 7]
    svg = body(vl.line({"a": ys}, unit="", smooth=0.5))
    assert [len(p) for p in bold(svg)] == [3, 3] and [len(p) for p in faint(svg)] == [3, 3]
    pts = [(float(i), y) for i, y in enumerate(ys)]
    assert [p for p in smoothed(pts, 0.5) if p[1] is not None] == smoothed([p for p in pts if p[1] is not None], 0.5)


def test_a_line_with_no_gaps_is_one_path_through_its_markers():
    svg = body(vl.line({"a": [1, 2, 3, 4], "b": [2, 3, 4, 5]}, runs={"a": [[1, 2, 3, 5]]}, unit=""))
    assert [len(p) for p in bold(svg)] == [4, 4] and len(markers(svg)) == 8
    assert [len(p) for p in faint(svg)] == [4] and run_dots(svg) == []
