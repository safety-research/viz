"""Tests for likert (diverging stacked bars for answers on an ordered scale) and table (a results table in the
booktabs look). Everything but the last test composes SVG without a browser."""
from __future__ import annotations

import html
import json
import os
import re
import subprocess
import sys
from collections import Counter
from dataclasses import dataclass

import pytest

import viz as vl
from viz import access, checks
from viz import theme as th
from viz.charts import likert as LK

SEVEN = range(-3, 4)
AGREE = ["Strongly disagree", "Disagree", "Neutral", "Agree", "Strongly agree"]
FEEL = {  # 100 answers per condition to "How do you feel about this task?", from -3 to +3; net 11, 67, -30
    "Repetitive task": [2, 7, 20, 31, 24, 13, 3],
    "Plain task": [1, 2, 6, 15, 36, 28, 12],
    "Rude user": [9, 19, 26, 22, 15, 7, 2],
}
COLS = ["MMLU", "GSM8K", "HumanEval", "MATH"]
BENCH = [
    vl.section("Open models"),
    ("Model A", [68.2, 79.4, 61.0, 38.4]),
    ("Model B", [71.6, 84.1, 66.5, 45.2]),
    ("Model C", [63.9, 72.8, 54.3, None]),
    vl.section("Closed models"),
    ("Model D", [78.3, 91.2, 74.8, 52.6]),
    ("Model E", [81.0, 89.7, 79.3, 58.9]),
]
CI = {"Model A": [(65.4, 71.0), (77.1, 81.7), (57.3, 64.7), (35.5, 41.3)],
      "Model B": [(68.9, 74.3), (82.0, 86.2), (62.9, 70.1), (42.3, 48.1)],
      "Model C": [(61.1, 66.7), (70.3, 75.3), (50.5, 58.1), None],
      "Model D": [(75.8, 80.8), (89.6, 92.8), (71.4, 78.2), (49.7, 55.5)],
      "Model E": [(78.6, 83.4), (88.0, 91.4), (76.1, 82.5), (56.0, 61.8)]}


@pytest.fixture(autouse=True)
def fresh():
    checks.reset()
    vl.set_roles()
    yield
    vl.set_defaults(theme="light")
    vl.set_roles()
    checks.reset()


def examples() -> dict[str, vl.Figure]:
    return {
        "likert": vl.likert(FEEL, scale=SEVEN, sort=True, title="A rude user moved 54% of answers below neutral"),
        "likert_agree": vl.likert({"Closed book": [22, 41, 18, 12, 7], "With search": [4, 9, 11, 38, 38]},
                                  scale=AGREE, frame="blog"),
        "likert_sections": vl.likert([vl.section("Tasks"), ("Plain task", FEEL["Plain task"]), vl.section("Users"),
                                      ("Rude user", FEEL["Rude user"])], scale=SEVEN, totals=False),
        "table": vl.table(BENCH, columns=COLS, ci=CI, highlight="Model B", roles={"intervention": "Model B"},
                          label_header="Model", title="Model B led the open models on every benchmark"),
        "table_units": vl.table({"Model A": [71.2, 3.21, 1850], "Model B": [64.0, 2.94, 1702]},
                                columns=["Accuracy", "Latency", "Elo"], unit={"Latency": " s", "Elo": ""},
                                decimals={"Latency": 1}, better={"Latency": "lower"}, frame="blog"),
    }


# ---------------------------------------------------------------------------------------------- reading the SVG

@dataclass
class Text:
    x: float
    y: float
    s: str
    size: float
    fill: str
    weight: int
    anchor: str


@dataclass
class Box:
    x0: float
    x1: float
    y0: float
    y1: float
    fill: str


@dataclass
class Line:
    x1: float
    y1: float
    x2: float
    y2: float
    stroke: str
    width: float


def texts(svg: str) -> list[Text]:
    out = []
    for m in re.finditer(r'<text x="(-?[\d.]+)" y="(-?[\d.]+)"([^>]*)>([^<]*)</text>', svg):
        a = m.group(3)
        get = lambda k, d=None: (re.search(rf' {k}="([^"]*)"', a) or [None, d])[1]
        out.append(Text(float(m.group(1)), float(m.group(2)), html.unescape(m.group(4)), float(get("font-size")),
                        get("fill"), int(get("font-weight", 400)), get("text-anchor", "start")))
    return out


def rects(svg: str) -> list[Box]:
    return [Box(float(x), float(x) + float(w), float(y), float(y) + float(h), f) for x, y, w, h, f in
            re.findall(r'<rect x="(-?[\d.]+)" y="(-?[\d.]+)" width="([\d.]+)" height="([\d.]+)"(?: rx="[\d.]+")? '
                       r'fill="([^"]+)"/>', svg)]


def ends(svg: str) -> list[Box]:
    """The rounded outer segments of a likert bar (svg.hbar paths)."""
    out = []
    for x0, y, neg, a, r, v, f in re.findall(r'<path d="M(-?[\d.]+),(-?[\d.]+) h(-?)([\d.]+) a([\d.]+),[\d.]+ 0 0 [01] '
                                             r'-?[\d.]+,[\d.]+ v([\d.]+)[^"]*" fill="([^"]+)"/>', svg):
        x0, w = float(x0), float(a) + float(r)
        out.append(Box(x0 - w if neg else x0, x0 if neg else x0 + w, float(y), float(y) + float(v) + 2 * float(r), f))
    return out


def lines(svg: str) -> list[Line]:
    return [Line(*map(float, (a, b, c, d)), s, float(w)) for a, b, c, d, s, w in
            re.findall(r'<line x1="(-?[\d.]+)" y1="(-?[\d.]+)" x2="(-?[\d.]+)" y2="(-?[\d.]+)" stroke="([^"]+)" '
                       r'stroke-width="([\d.]+)"', svg)]


def likert_body(*args, **kw):
    return vl.likert(*args, **kw).body(960)


# ---------------------------------------------------------------------------------------------- both charts

def test_registered():
    for k in ("likert", "table"):
        assert k in vl.CHARTS and k in vl.__all__ and callable(getattr(vl, k))


@pytest.mark.parametrize("name", list(examples()))
def test_renders_clean_and_deterministic_svg(name):
    a, b = examples()[name], examples()[name]
    svg = a.svg()
    assert svg.startswith("<svg") and svg.endswith("</svg>")
    for bad in ("NaN", "nan", "None", "inf"):
        assert bad not in re.sub(r">[^<]*<", "><", svg), bad
    assert svg == b.svg() == a.svg()  # fresh builds agree, and rendering twice changes nothing


def test_deterministic_across_processes():
    here = os.path.dirname(__file__)
    code = (f"import hashlib, sys; sys.path.insert(0, {here!r}); from test_likert_table import examples; "
            "print(hashlib.sha256(''.join(f.svg() for f in examples().values()).encode()).hexdigest())")
    digests = set()
    for seed in ("1", "2"):
        env = dict(os.environ, PYTHONHASHSEED=seed)
        digests.add(subprocess.run([sys.executable, "-c", code], env=env, capture_output=True, text=True,
                                   check=True).stdout.strip())
    assert len(digests) == 1


def test_json_specs_round_trip():
    specs = [
        {"chart": "likert", "data": {"A": [1, 2, 3, 4, 5], "B": [5, 4, 3, 2, 1]}, "scale": AGREE, "neutral": "Neutral",
         "sort": True},
        {"chart": "table", "rows": [{"section": "Open"}, ["A", [71.2, None]], {"section": "Closed"}, ["B", [80.4, 3.1]]],
         "columns": ["Accuracy", "Latency"], "unit": {"Latency": " s"}, "decimals": {"Latency": 1},
         "better": {"Latency": "lower"}, "ci": {"A": [[69, 73.4], None]}, "highlight": "B"},
    ]
    for s in specs:
        fig = vl.from_spec(json.loads(json.dumps(s)))
        assert fig.kind == s["chart"] and fig.svg() == vl.from_spec(s).svg()


def test_dark_theme_pngs_render(tmp_path):
    vl.set_defaults(theme="dark")
    for name in ("likert", "table"):
        p = examples()[name].save(tmp_path / f"{name}.png")  # -W error::viz.checks.VizCheck: no check fires
        assert p.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"


# ---------------------------------------------------------------------------------------------- likert

def test_likert_puts_low_answers_left_high_right_and_the_neutral_across_the_center():
    body = likert_body(FEEL, scale=SEVEN)
    svg = body.svg
    center = [ln for ln in lines(svg) if ln.stroke == th.AXIS]
    assert len(center) == 1 and center[0].x1 == center[0].x2
    cx = center[0].x1
    fills = LK.fills(7, 3)
    segs = rects(svg) + ends(svg)
    assert len(segs) == 3 * 7 and {s.fill for s in segs} == set(fills)
    for s in segs:
        j = fills.index(s.fill)
        if j == 3:  # the neutral share: half on each side (the 0.4 px overlap hides seams)
            assert abs((s.x0 + s.x1 - 0.4) / 2 - cx) < 0.05
        elif j < 3:
            assert s.x1 <= cx + 0.5
        else:
            assert s.x0 >= cx - 0.5
    for y in {s.y0 for s in segs}:  # each bar runs in scale order, left to right
        row = sorted((s for s in segs if s.y0 == y), key=lambda s: s.x0)
        assert [fills.index(s.fill) for s in row] == list(range(7))
    assert body.legend == list(zip(["−3", "−2", "−1", "0", "+1", "+2", "+3"], fills))  # one row, scale order


def test_likert_shows_each_row_as_percent_of_its_answers_with_totals_at_the_ends():
    shares = likert_body(FEEL, scale=SEVEN).svg
    counts = likert_body({k: [3 * v for v in vs] for k, vs in FEEL.items()}, scale=SEVEN).svg
    assert counts == shares
    ts = texts(shares)
    cx = next(ln.x1 for ln in lines(shares) if ln.stroke == th.AXIS)
    inside = [t.s for t in ts if t.size == 12 and t.weight == 600]
    assert {"36%", "28%", "31%", "26%"} <= set(inside)
    totals = [t for t in ts if t.size == 13 and t.weight == 600]
    low = {t.s for t in totals if t.anchor == "end" and t.x < cx}
    high = {t.s for t in totals if t.anchor == "start" and t.x > cx}
    assert low == {"29%", "9%", "54%"} and high == {"40%", "76%", "24%"}
    assert {t.fill for t in totals} == {th.readable("coral"), th.readable("blue")}
    ticks = [t.s for t in ts if t.size == th.TICK_SIZE and t.fill == th.MUTED]
    assert ticks == ["75%", "50%", "25%", "0%", "25%", "50%", "75%", "100%"]  # absolute percents, 0 at the center


def test_likert_options():
    order = lambda svg: [t.s for t in texts(svg) if t.anchor == "end" and t.size == 13.5]
    assert order(likert_body(FEEL, scale=SEVEN).svg) == ["Repetitive task", "Plain task", "Rude user"]
    assert order(likert_body(FEEL, scale=SEVEN, sort=True).svg) == ["Plain task", "Repetitive task", "Rude user"]
    assert order(likert_body(FEEL, scale=SEVEN, sort="asc").svg) == ["Rude user", "Repetitive task", "Plain task"]
    quiet = likert_body(FEEL, scale=SEVEN, totals=False, values=False).svg
    assert not [t for t in texts(quiet) if t.weight == 600]
    assert "36.0%" in likert_body(FEEL, scale=SEVEN, decimals=1).svg
    # neutral: an odd scale's middle by default, by its label or its number; an even scale splits in half
    auto = likert_body(FEEL, scale=SEVEN).svg
    assert likert_body(FEEL, scale=SEVEN, neutral=0).svg == likert_body(FEEL, scale=SEVEN, neutral="0").svg == auto
    even = likert_body({"A": [10, 20, 30, 40]}, scale=["Never", "Rarely", "Often", "Always"])
    assert th.color("beige") not in even.svg and [c for _, c in even.legend] == LK.fills(4, None)
    off = likert_body({"A": [1, 2, 3, 4, 5]}, scale=["Bad", "Neutral", "Fine", "Good", "Great"], neutral="Neutral")
    assert [c for _, c in off.legend] == LK.shades("coral", 1) + [th.color("beige")] + LK.shades("blue", 3)
    # numbers: a true minus, and a plus only when the scale has negatives
    assert [lab for lab, _ in likert_body({"A": [1] * 5}, scale=range(1, 6)).legend] == ["1", "2", "3", "4", "5"]
    # answers counted per scale point, such as a Counter
    assert (likert_body({"A": Counter([-1, -1, 0, 3, 3, 3, 3])}, scale=SEVEN).svg
            == likert_body({"A": [0, 0, 2, 1, 0, 0, 4]}, scale=SEVEN).svg)
    # high answers that are the bad ones: swap the sides' colors
    swapped = likert_body(FEEL, scale=SEVEN, low="blue", high="coral")
    assert [c for _, c in swapped.legend] == LK.fills(7, 3, "blue", "coral")
    # sections, and a row with no answers
    sec = texts(likert_body([vl.section("Tasks"), ("Plain task", FEEL["Plain task"]), vl.section("Users"),
                             ("Rude user", FEEL["Rude user"]), ("Nobody", [0] * 7)], scale=SEVEN).svg)
    assert [t.s for t in sec if t.fill == th.MUTED and t.weight == 600] == ["Tasks", "Users"]
    assert "no answers" in [t.s for t in sec]


@pytest.mark.parametrize("data, kw, match", [
    ({"A": [1, 2]}, {"scale": "agree"}, "scale"),
    ({"A": [1]}, {"scale": ["Only"]}, "at least two"),
    ({"A": [1, 2]}, {"scale": ["Yes", "Yes"]}, "at least two different"),
    ({"A": [1, 2, 3]}, {"scale": ["No", "Unsure", "Yes"], "neutral": "Maybe"}, "isn't one of"),
    ({"A": [1, 2]}, {"scale": ["No", "Unsure", "Yes"]}, "has 2 values for the 3 points"),
    ({"A": [1, -2, 3]}, {"scale": ["No", "Unsure", "Yes"]}, "negative"),
    ({"A": Counter({5: 1})}, {"scale": SEVEN}, "aren't on the scale"),
    ([vl.section("S"), ("A", [1, 2, 3])], {"scale": ["No", "Unsure", "Yes"], "sort": True}, "sections"),
    ([vl.section("S")], {"scale": ["No", "Yes"]}, "at least one row"),
])
def test_likert_errors(data, kw, match):
    with pytest.raises(ValueError, match=match):
        vl.likert(data, **kw)


@pytest.mark.parametrize("theme", ["light", "dark"])
def test_likert_shades_stay_apart_and_strengthen_toward_the_extremes(theme):
    vl.set_defaults(theme=theme)
    strength = lambda c: access.contrast(c, th.BG)
    for n in range(2, 12):
        mid = n // 2 if n % 2 else None
        fs = LK.fills(n, mid)
        for a, b in zip(fs, fs[1:]):
            assert access.delta_e(a, b) >= 8, (n, a, b)
            assert access.worst_delta_e(a, b)[0] >= 7, (n, a, b)  # the library's floor for ordered colors
        k = mid if mid is not None else n // 2
        low, high = fs[:k], fs[n - k:]
        assert all(strength(a) > strength(b) for a, b in zip(low, low[1:])), (n, low)
        assert all(strength(a) < strength(b) for a, b in zip(high, high[1:])), (n, high)
        if mid is not None:
            assert fs[mid] == th.color("beige")
    # three- and five-point scales end in the outcome colors themselves
    assert LK.fills(3, 1) == [th.color("coral"), th.color("beige"), th.color("blue")]
    assert LK.fills(5, 2)[0] == th.color("coral") and LK.fills(5, 2)[-1] == th.color("blue")


@pytest.mark.parametrize("theme", ["light", "dark"])
def test_likert_text_reaches_4_5_to_1_and_12_px(theme):
    vl.set_defaults(theme=theme)
    svg = likert_body(FEEL, scale=SEVEN, sort=True).svg
    segs = rects(svg) + ends(svg)
    for t in texts(svg):
        under = next((s.fill for s in segs if s.x0 <= t.x <= s.x1 and s.y0 <= t.y - 4 <= s.y1), th.BG)
        assert access.contrast(t.fill, under) >= 4.5, (theme, t.s, t.fill, under)
        assert t.size >= th.MIN_TEXT


def test_likert_alt_text_gives_every_share_and_the_totals():
    f = vl.likert(FEEL, scale=SEVEN, sort=True, title="A rude user moved 54% of answers below neutral")
    alt = f.alt_text()
    assert alt.startswith("A rude user moved 54% of answers below neutral. Diverging stacked bars of answers from "
                          "−3 to +3, 0 as neutral. ")
    assert ("Plain task: −3 1%, −2 2%, −1 6%, 0 15%, +1 36%, +2 28%, +3 12% (9% below the middle, 76% above it)"
            in alt)
    assert alt.index("Plain task") < alt.index("Repetitive task") < alt.index("Rude user")  # the drawn order
    sec = vl.likert([vl.section("Users"), ("Rude user", FEEL["Rude user"]), ("Nobody", [0] * 7)], scale=SEVEN)
    assert "Users: Rude user: −3 9%" in sec.alt_text() and "Nobody: no answers" in sec.alt_text()


def test_likert_checks():
    title = "A rude user moved 54% of answers below neutral"
    assert vl.likert(FEEL, scale=SEVEN, sort=True, title=title).check() == []
    out = vl.likert(FEEL, scale=SEVEN, title=title).check()  # rows out of net order
    assert any("aren't in order of their values" in p for p in out)
    assert vl.likert(FEEL, scale=SEVEN, sort=False, title=title).check() == []


def test_likert_in_the_dark_theme():
    title = "A rude user moved 54% of answers below neutral"
    light, light_fills = vl.likert(FEEL, scale=SEVEN, sort=True, title=title).svg(), LK.fills(7, 3)
    vl.set_defaults(theme="dark")
    f = vl.likert(FEEL, scale=SEVEN, sort=True, title=title)
    svg = f.svg()
    dark_fills = LK.fills(7, 3)
    assert svg != light and th.BG in svg and all(c in svg for c in dark_fills)
    assert dark_fills != light_fills and dark_fills[3] == th.color("beige")  # mixed with the theme's own tokens
    assert f.check() == []


def test_likert_fits_narrow_sizes():
    f = vl.likert({"A much longer condition name that wraps": Counter([3, 2, 2, 1, 1, 0, -1, -2]),
                   "Short": Counter([0, 1, -1])}, scale=SEVEN, size="column", title="Answers by condition")
    body = f.body(f._width())
    assert max(t.x for t in texts(body.svg) if t.anchor == "start") < f._width()
    ticks = [t.s for t in texts(body.svg) if t.size == th.TICK_SIZE and t.fill == th.MUTED]
    assert ticks == ["50%", "0%", "50%", "100%"]  # halves where quarters would crowd
    assert f.check() == []


# ---------------------------------------------------------------------------------------------- table

def table_body(*args, **kw):
    return vl.table(*args, **kw).body(960)


def test_table_draws_three_rules_and_no_vertical_lines():
    body = table_body(BENCH, columns=COLS, label_header="Model")
    ls = lines(body.svg)
    assert all(ln.y1 == ln.y2 for ln in ls)  # rules only
    heavy = [ln for ln in ls if ln.width == 1.2]
    mid = [ln for ln in ls if ln.width == 0.75 and ln.stroke == th.INK]
    assert len(heavy) == 2 and len(mid) == 1 and {ln.stroke for ln in heavy} == {th.INK}
    assert heavy[0].y1 < mid[0].y1 < heavy[1].y1  # above the header, under it, at the bottom
    assert [ln for ln in ls if ln.stroke == th.AXIS]  # a light rule between the two groups
    assert heavy[0].x1 == 0 and heavy[0].x2 == pytest.approx(960)  # a typical table spans the figure
    assert "font-variant-numeric:tabular-nums" in body.svg


def test_table_aligns_labels_left_and_numbers_right():
    ts = texts(table_body(BENCH, columns=COLS, label_header="Model").svg)
    labels = [t for t in ts if t.s.startswith("Model")]
    assert [t.s for t in labels] == ["Model", "Model A", "Model B", "Model C", "Model D", "Model E"]
    assert {t.anchor for t in labels} == {"start"} and len({t.x for t in labels}) == 1
    values = [t for t in ts if t.s.endswith("%") or t.s == "—"]
    assert len(values) == 20 and {t.anchor for t in values} == {"end"}
    assert len({t.x for t in values}) == 4  # one right edge per column
    assert [t.s for t in ts if t.anchor == "middle"] == COLS
    assert [t.s for t in ts if t.fill == th.MUTED and t.weight == 600] == ["Open models", "Closed models"]
    assert next(t for t in values if t.s == "—").fill == th.MUTED  # None prints an em dash


def test_the_best_value_in_each_column_is_bold():
    bold = lambda body: sorted(t.s for t in texts(body.svg) if t.weight == 600 and t.anchor == "end")
    assert bold(table_body(BENCH, columns=COLS)) == sorted(["81.0%", "91.2%", "79.3%", "58.9%"])
    assert bold(table_body(BENCH, columns=COLS, better={"MATH": "lower", "MMLU": None})) == sorted(["91.2%", "79.3%", "38.4%"])
    assert bold(table_body(BENCH, columns=COLS, better="lower")) == sorted(["63.9%", "72.8%", "54.3%", "38.4%"])
    ties = table_body({"A": [71.4, 50], "B": [71.4, 50], "C": [60.0, 50]}, columns=["x", "y"])
    assert bold(ties) == ["71.4%", "71.4%"]  # both are the best; a column that reads the same throughout has none


def test_intervals_read_plus_minus_when_symmetric_and_as_brackets_when_not():
    sym = table_body({"A": [71.3, 40.0], "B": [65.0, 52.0]}, columns=["x", "y"],
                     ci={"A": [(68.3, 74.3), (37.0, 43.0)], "B": [(62.0, 68.0), None]})
    ts = texts(sym.svg)
    pm = [t for t in ts if t.s.startswith("±")]
    assert [t.s for t in pm] == ["±3.0", "±3", "±3.0"] and {(t.size, t.fill) for t in pm} == {(12, th.MUTED)}
    value = next(t for t in ts if t.s == "71.3%")
    assert pm[0].x > value.x and pm[0].anchor == "start" and pm[0].y == value.y  # right after its value
    asym = [t.s for t in texts(table_body({"A": [71.3], "B": [65.0]}, columns=["x"],
                                          ci={"A": (60.0, 75.0), "B": (62.0, 68.0)}).svg)]
    assert "[60.0, 75.0]" in asym and "[62.0, 68.0]" in asym  # one form for the whole table
    narrow = [t.s for t in texts(table_body({"A": [71.3]}, columns=["x"], ci={"A": (71.1, 71.5)}).svg)]
    assert "±0.2" in narrow  # enough decimals to show the interval


def test_highlight_sets_the_row_on_a_tint_of_its_role_color():
    plain = table_body(BENCH, columns=COLS, highlight="Model E").svg
    assert [r.fill for r in rects(plain)] == [th.TINT["coral"]]  # the accent's tint
    roled = table_body(BENCH, columns=COLS, highlight="Model B", roles={"intervention": "Model B"}).svg
    assert [r.fill for r in rects(roled)] == [th.TINT["coral"]]
    label = next(t for t in texts(roled) if t.s == "Model B")
    assert label.weight == 600 and label.fill == th.INK
    band = rects(roled)[0]
    assert band.x0 == 0 and band.x1 == pytest.approx(960) and band.y0 < label.y < band.y1
    assert not rects(table_body(BENCH, columns=COLS).svg)
    with pytest.raises(ValueError, match="Model Z"):
        vl.table(BENCH, columns=COLS, highlight="Model Z")


def test_units_decimals_and_formats_per_column():
    ts = {t.s for t in texts(examples()["table_units"].body(960).svg)}
    assert {"71.2%", "64.0%", "3.2 s", "2.9 s", "1,850", "1,702"} <= ts
    assert "0.712" in {t.s for t in texts(table_body({"A": [0.712]}, columns=["Score"], unit="", fmt="{:.3f}").svg)}
    assert {"71.2%", "64.0%"} <= {t.s for t in texts(table_body({"A": [71.2], "B": [64.0]}, columns=["x"],
                                                                  decimals=1).svg)}


def test_table_inputs():
    a = table_body({"Model A": {"MMLU": 71, "GSM8K": 84}, "Model B": {"GSM8K": 80, "MMLU": 69}}).svg  # columns from keys
    b = table_body({"Model A": [71, 84], "Model B": [69, 80]}, columns=["MMLU", "GSM8K"]).svg
    assert a == b
    one = texts(table_body({"Model A": 71, "Model B": 69}, columns=["MMLU"]).svg)
    assert [t.s for t in one if t.anchor == "end"] == ["71%", "69%"]


def test_dataframes():
    pd = pytest.importorskip("pandas")
    df = pd.DataFrame({"MMLU": [71, 69], "GSM8K": [84, 80]}, index=pd.Index(["Model A", "Model B"], name="Model"))
    svg = table_body(df).svg
    assert ">Model<" in svg and ">GSM8K<" in svg  # the index name heads the label column, the columns the rest
    assert table_body(df, label_header="").svg != svg
    answers = pd.DataFrame([[1, 2, 6, 15, 36, 28, 12]], index=["Plain task"], columns=list(SEVEN))
    assert likert_body(answers, scale=SEVEN).svg == likert_body({"Plain task": FEEL["Plain task"]}, scale=SEVEN).svg


@pytest.mark.parametrize("rows, kw, match", [
    ({"A": [1, 2]}, {}, "pass columns"),
    ({"A": [1, 2]}, {"columns": ["x"]}, "1 columns for 2 values"),
    ({"A": [1, 2]}, {"columns": ["x", "y"], "better": {"z": "lower"}}, "better names columns"),
    ({"A": [1, 2]}, {"columns": ["x", "y"], "better": "smaller"}, "higher"),
    ({"A": [1, 2]}, {"columns": ["x", "y"], "unit": {"z": ""}}, "unit names columns"),
    ({"A": [1, 2]}, {"columns": ["x", "y"], "ci": {"B": [(0, 2), None]}}, "ci names rows"),
    ({"A": [1, 2]}, {"columns": ["x", "y"], "ci": {"A": [(0, 2)]}}, "1 intervals for 2 columns"),
    ({"A": [1, 2]}, {"columns": ["x", "y"], "ci": {"A": (0, 2)}}, "ci"),
    ({"A": [1, 2]}, {"columns": ["x", "y"], "highlight": "B"}, "highlight"),
    ([vl.section("Only a heading")], {"columns": ["x"]}, "at least one row"),
])
def test_table_errors(rows, kw, match):
    with pytest.raises(ValueError, match=match):
        vl.table(rows, **kw)


def test_table_alt_text():
    f = vl.table(BENCH, columns=COLS, ci=CI, title="Model E scored highest on three of the four benchmarks")
    alt = f.alt_text()
    assert alt.startswith("Model E scored highest on three of the four benchmarks. Table of 5 rows by 4 columns "
                          "(MMLU, GSM8K, HumanEval, MATH; bold marks the best in each column). ")
    assert "Open models: Model A: MMLU 68.2% (interval 65.4% to 71.0%), GSM8K 79.4% (interval 77.1% to 81.7%)" in alt
    assert "HumanEval 54.3% (interval 50.5% to 58.1%), MATH no value;" in alt
    assert "Closed models: Model D:" in alt and "GSM8K 91.2% (interval 89.6% to 92.8%) (best)" in alt


def test_table_with_a_plain_title_passes_the_checks():
    f = vl.table(BENCH, columns=COLS, ci=CI, highlight="Model E", label_header="Model",
                 title="Model E scored highest on three of the four benchmarks")
    assert f.check() == []


@pytest.mark.parametrize("theme", ["light", "dark"])
def test_table_text_reaches_4_5_to_1_on_its_background(theme):
    vl.set_defaults(theme=theme)
    f = vl.table(BENCH, columns=COLS, ci=CI, highlight=["Model B", "Model E"], roles={"intervention": "Model B"},
                 title="Model B led the open models on every benchmark")
    body = f.body(960)
    bands = rects(body.svg)
    assert len(bands) == 2 and bands[0].fill != bands[1].fill
    for t in texts(body.svg):
        under = next((b.fill for b in bands if b.y0 <= t.y <= b.y1), th.BG)
        assert access.contrast(t.fill, under) >= 4.5, (theme, t.s, t.fill, under)
        assert t.size >= th.MIN_TEXT
    assert f.check() == []
    if theme == "dark":
        assert th.BG in f.svg() and {ln.stroke for ln in lines(body.svg) if ln.width == 1.2} == {th.INK}


def test_a_narrow_table_centers_under_a_blog_title():
    data = {"Closed book": [41.0, 12.5], "With search": [88.0, 2.4]}
    claim = table_body(data, columns=["Correct", "Refused"]).meta["plot_x"]
    blog = table_body(data, columns=["Correct", "Refused"], frame="blog").meta["plot_x"]
    assert claim[0] == 0 and claim[1] < 960
    assert blog[0] > 0 and blog[0] == pytest.approx(960 - blog[1])


def test_long_headers_wrap_to_two_lines_and_the_table_stays_inside():
    f = vl.table({"Qwen3-8B": [61.2, 70.4, 0.71, 3.2, 1850], "Llama 3.1 8B Instruct": [58.9, 66.0, 0.64, 2.9, 1702],
                  "Gemma 4 31B": [74.1, 81.3, 0.80, 7.6, 2210]},
                 columns=["Correct answers", "Refusals avoided", "Calibration (ECE)", "Seconds per answer", "Elo rating"],
                 better={"Calibration (ECE)": "lower", "Seconds per answer": "lower"},
                 unit={"Calibration (ECE)": "", "Seconds per answer": " s", "Elo rating": ""},
                 decimals={"Calibration (ECE)": 2, "Seconds per answer": 1}, size="paper",
                 title="Gemma 4 31B answered the most questions correctly")
    body = f.body(f._width())
    heads = [t for t in texts(body.svg) if t.anchor == "middle"]
    assert len({t.y for t in heads}) == 2 and "Correct answers" in [t.s for t in heads]
    assert max(ln.x2 for ln in lines(body.svg)) <= f._width() + 1e-6
    assert f.check() == []
