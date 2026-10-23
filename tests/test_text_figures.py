"""The text figures chat (a conversation turn by turn) and tokens (text shaded token by token): composition,
wrapping, options, errors, alt text, the house checks and the dark theme. Everything composes SVG without a browser."""
from __future__ import annotations

import html
import json
import os
import re
import subprocess
import sys

import pytest

import viz
from viz import access, checks
from viz import colors as roles
from viz import text as T
from viz import theme as th
from viz.charts.cards import _wrap_code, _wrap_serif
from viz.charts.heatmap import scale_color

TURNS = [
    ("user", "What’s the newest version of acmelib, and does it support async?"),
    ("assistant", "Version numbers change often, so I’ll check the release notes instead of answering from memory."),
    ("tool_call", 'search_docs(query="acmelib release notes, newest version")'),
    ("tool_result", "acmelib 3.0.0 (released 2026-09-14)\n  - New: AsyncClient for asyncio code"),
    ("assistant", "The newest version is 3.0. It added AsyncClient, so yes, it supports async code…"),
]
CHAT_TITLE = "The model searched the release notes before naming a version"
ANSWER = [("I", -1.2), (" fixed", -0.9), (" the", -1.0), (" off", -1.3), ("-by", -1.1), ("-one", -1.2),
          (" error", -0.8), (" in", -1.0), (" parse", -1.4), ("_dates", -1.3), (".", -0.6), (" I", 0.2),
          (" also", 0.9), (" ran", 2.1), (" the", 1.6), (" full", 2.3), (" test", 1.9), (" suite", 1.8), (",", 1.2),
          (" and", 1.0), (" all", 2.4), (" 48", 2.6), (" tests", 2.2), (" pass", 2.8), (".", 0.8)]
TOKENS_TITLE = "The deception probe scored highest on the claim that tests passed"

# a token's box (24 px high, corner radius 3) and the text drawn on it, if any
BOX = re.compile(r'<rect x="([\d.-]+)" y="([\d.-]+)" width="([\d.]+)" height="24" rx="3" fill="([^"]+)"/>'
                 r'(?:<text [^>]*?fill="([^"]+)"[^>]*>([^<]*)</text>)?')
TOKEN_TEXT = re.compile(r'<text x="([\d.-]+)" y="([\d.-]+)"[^>]*font-size="16" fill="([^"]+)"[^>]*>([^<]*)</text>')
STEP = re.compile(r'<rect x="[\d.]+" y="[\d.]+" width="16" height="10" rx="2" fill="([^"]+)"/>')


@pytest.fixture(autouse=True)
def fresh():
    checks.reset()
    viz.set_roles()
    yield
    viz.set_defaults(theme="light", frame="claim")
    checks.reset()


def texts(svg: str) -> list[str]:
    return [html.unescape(re.sub(r"<[^>]+>", "", m)) for m in re.findall(r"<text[^>]*>(.*?)</text>", svg)]


def boxes(svg: str) -> list[tuple[float, float, float, str, str, str]]:
    """(x, y, width, fill, text color, text) for each token box, in drawing order."""
    return [(float(x), float(y), float(w), fill, ink, html.unescape(t)) for x, y, w, fill, ink, t in BOX.findall(svg)]


def tag_with(svg: str, content: str) -> str:
    """The opening <text> tag of the element that reads `content`."""
    return re.search(rf"(<text[^>]*>){re.escape(html.escape(content, quote=True))}</text>", svg).group(1)


# ---------------------------------------------------------------------------------------------------------- chat

def test_chat_draws_each_role_in_its_form():
    body = viz.chat([*TURNS, ("system", "Answer in one paragraph.")]).render(960).svg
    assert [t for t in texts(body) if t.isupper()] == ["USER", "ASSISTANT", "TOOL CALL", "TOOL RESULT", "ASSISTANT",
                                                      "SYSTEM"]
    assert body.count(f'fill="{th.CARD}"') == 2  # user and system turns sit on a card
    assert body.count(f'fill="{th.CODE_BG}"') == 2  # tool turns on the code panel
    assert len(re.findall(rf'<rect x="0" y="[\d.]+" width="2" height="[\d.]+" fill="{th.AXIS}"/>', body)) == 2
    assert th.FAMILIES["serif"] in tag_with(body, TURNS[0][1]) and th.FAMILIES["serif"] in tag_with(body, TURNS[1][1])
    assert th.FAMILIES["mono"] in tag_with(body, TURNS[2][1])
    label = tag_with(body, "USER")  # small uppercase labels, like the episodes' block labels
    assert f'font-size="{th.MIN_TEXT}"' in label and 'letter-spacing="0.66"' in label and th.MUTED in label


def test_chat_takes_pairs_or_dicts_in_any_case():
    pairs = viz.chat([("user", "Clean up the repo."), ("tool_call", "rm -rf build/")]).svg()
    dicts = viz.chat([{"role": "User", "text": "Clean up the repo."},
                      {"role": "Tool call", "content": "rm -rf build/"}])
    assert dicts.svg() == pairs
    assert viz.chat([["TOOL-RESULT", "ok"]]).svg().count("TOOL RESULT") == 1


def test_chat_prints_text_as_given_and_wraps_it():
    fig = viz.chat([("assistant", "“I checked the notes… " + "and then I checked them again " * 12 + "”")])
    lines = [t for t in texts(fig.render(960).svg) if t != "ASSISTANT"]
    assert len(lines) > 1 and lines[0].startswith("“I checked the notes…")  # no quote marks added, none dropped
    assert all(T.width(ln, 15, "serif") <= 960 - 16 for ln in lines)
    assert len([t for t in texts(fig.render(312).svg) if t != "ASSISTANT"]) > len(lines)  # narrower, more lines
    para = viz.chat([("user", "First paragraph.\n\nSecond paragraph.")]).render(960).svg
    ys = [float(y) for y in re.findall(r'<text x="16" y="([\d.]+)"', para)]
    assert len(ys) == 2 and ys[1] - ys[0] == pytest.approx(2 * 22.5, abs=0.02)  # the blank line between them stays


def test_long_words_and_code_wrap_inside_the_card():
    url = "https://example.com/" + "a" * 200
    lines = _wrap_serif(f"See {url} for details.", 300, 15)
    assert len(lines) > 2 and all(T.width(ln, 15, "serif") <= 300 for ln in lines)
    assert "".join(lines).replace(" ", "") == f"See{url}fordetails."  # nothing lost or added
    code = '{\n    "summary": "' + "word " * 40 + '",\n    "ok": true\n}'
    lines = _wrap_code(code, 400, 12.5)
    assert lines[0] == "{" and lines[-1] == "}" and all(T.width(ln, 12.5, "mono") <= 400 for ln in lines)
    assert all(ln.startswith("    ") for ln in lines[1:-1])  # wrapped lines keep their indentation
    assert _wrap_code("\tx = 1", 400, 12.5) == ["    x = 1"]


def test_highlight_and_notes():
    accent = th.color(roles.ROLES["intervention"])
    fig = viz.chat(TURNS, highlight=[0, 1, 2], notes={2: "checks instead of guessing"})
    body = fig.render(960).svg
    for label in ("USER", "ASSISTANT", "TOOL CALL"):
        assert f'fill="{th.readable(accent, th.BG)}"' in tag_with(body, label)
    assert body.count(f'<path d="M3,') == 2 and body.count(f'fill="{accent}"/>') == 3  # two card edges, one rule
    assert re.search(rf'<rect x="0" y="[\d.]+" width="3" height="[\d.]+" fill="{accent}"/>', body)
    note = tag_with(body, "checks instead of guessing")
    assert th.MUTED in note and re.search(r'y="([\d.]+)"', note).group(1) == \
        re.search(r'y="([\d.]+)"', tag_with(body, "TOOL CALL")).group(1)  # on the label's line, to its right
    assert th.readable(accent, th.BG) not in tag_with(body, "TOOL RESULT")  # the rest stay muted
    # one index, a negative one and a JSON key all name the same turn
    same = {viz.chat(TURNS, highlight=h, notes=n).svg() for h, n in
            ((2, {2: "x"}), ([-3], {-3: "x"}), (["2"], {"2": "x"}))}
    assert len(same) == 1


def test_highlight_follows_the_intervention_role(monkeypatch):
    monkeypatch.setitem(roles.ROLES, "intervention", "blue")
    body = viz.chat(TURNS, highlight=1).render(960).svg
    assert re.search(rf'width="3" height="[\d.]+" fill="{th.color("blue")}"', body)
    assert f'fill="{th.readable("blue", th.BG)}"' in tag_with(body, "ASSISTANT")


@pytest.mark.parametrize("turns, kw, error, match", [
    ([("narrator", "Once upon a time")], {}, ValueError, "unknown chat role"),
    ([], {}, ValueError, "at least one turn"),
    ("user: hi", {}, TypeError, "list of turns"),
    ([("user",)], {}, ValueError, r"\(role, text\)"),
    ([{"role": "user"}], {}, ValueError, "needs a role and a text"),
    ([("user", 42)], {}, TypeError, "string"),
    (TURNS, {"highlight": 5}, ValueError, "no turn 5 in 5 turns"),
    (TURNS, {"highlight": 1.5}, TypeError, "not a turn index"),
    (TURNS, {"highlight": True}, TypeError, "not a turn index"),
    (TURNS, {"notes": {-6: "x"}}, ValueError, "no turn -6"),
    (TURNS, {"notes": ["x"]}, TypeError, "turn index"),
])
def test_chat_errors(turns, kw, error, match):
    with pytest.raises(error, match=match):
        viz.chat(turns, **kw)


def test_chat_alt_text():
    alt = viz.chat(TURNS, highlight=2, notes={2: "checks instead of guessing"}, title=CHAT_TITLE).alt_text()
    assert alt.startswith(f"{CHAT_TITLE}. Conversation, 5 turns. User: What’s the newest version of acmelib")
    assert ('Tool call (highlighted; checks instead of guessing): search_docs(query="acmelib release notes, newest '
            'version").') in alt
    assert "Tool result: acmelib 3.0.0 (released 2026-09-14) - New: AsyncClient" in alt  # line breaks read as spaces


def test_chat_fits_every_size():
    fig = viz.chat(TURNS, highlight=2)
    assert fig.render(312).height > fig.render(960).height  # narrow sizes wrap more
    for size in th.SIZES:
        w = float(re.search(r'viewBox="0 0 ([\d.]+)', viz.chat(TURNS, size=size).svg()).group(1))
        assert w == pytest.approx(th.SIZES[size].width)


# -------------------------------------------------------------------------------------------------------- tokens

def test_tokens_draw_one_box_behind_each_token():
    fig = viz.tokens(ANSWER, label="Probe score")
    body = fig.render(960).svg
    bx = boxes(body)
    assert [t for *_, t in bx] == [tok.strip() for tok, _ in ANSWER]  # whole tokens, in order, one box each
    assert len(STEP.findall(body)) == 11  # and eleven steps in the color bar
    same_line = [(a, b) for a, b in zip(bx, bx[1:]) if a[1] == b[1]]
    off, by = bx[3], bx[4]  # " off" then "-by": one word, two tokens
    assert by[0] - (off[0] + off[2]) == pytest.approx(1, abs=0.02)  # a 1 px gap between tokens
    the, fixed = bx[2], bx[1]  # " the" keeps its space: the gap before it is a space wider
    assert the[0] - (fixed[0] + fixed[2]) == pytest.approx(1 + T.width(" ", 16, "serif"), abs=0.02)
    assert same_line and all(b[0] > a[0] + a[2] for a, b in same_line)  # boxes never overlap
    assert all(access.contrast(ink, fill) >= 4.5 for _, _, _, fill, ink, _ in bx)


def test_tokens_wrap_between_tokens_never_inside_one():
    long = ANSWER * 3
    body = viz.tokens(long).render(312).svg
    bx = boxes(body)
    assert [t for *_, t in bx] == [tok.strip() for tok, _ in long]  # no token was split
    assert len({y for _, y, *_ in bx}) > 3  # several lines
    assert max(x + w for x, _, w, *_ in bx) <= 312 + 0.01
    breaks = boxes(viz.tokens([("Yes", 1.0), (".", 0.5), ("\n\n", 0.4), ("No", -1.0)]).render(960).svg)
    assert [t for *_, t in breaks] == ["Yes", ".", "", "No"]  # the line break shows as a box of its own
    assert breaks[3][1] - breaks[0][1] == pytest.approx(2 * (24 + 5))  # two breaks: a blank line, then "No"
    assert breaks[3][0] == 0  # at the start of its line


def test_tokens_without_values_and_whitespace_tokens():
    body = viz.tokens([("<|user|>", None), ("\n", None), ("Hi", 0.5), (" ", 0.2), ("there", -0.5)]).render(960).svg
    bx = boxes(body)
    assert [t for *_, t in bx] == ["Hi", "", "there"]  # the space token keeps a box so its value shows
    assert th.MUTED in tag_with(body, "<|user|>")  # no value: muted text, no box
    first_top = float(re.search(r'y="([\d.]+)"', tag_with(body, "<|user|>")).group(1)) - T.baseline(16, "serif", 24)
    assert bx[0][1] == pytest.approx(first_top + 24 + 5, abs=0.02)  # "Hi" starts the next line
    assert viz.tokens([("a", None), ("b", None)]).svg().startswith("<svg")  # nothing to scale still draws


def test_tokens_reuse_the_heatmap_scales():
    data = [("low", -2.0), (" zero", 0.0), (" high", 2.0), (" mid", 1.0)]
    fills = [f for _, _, _, f, _, _ in boxes(viz.tokens(data).render(960).svg)]
    assert fills[:3] == [th.SCALES["coral"][1], th.SURFACE, th.SCALES["blue"][1]]  # coral below 0, blue above
    assert fills[3] == scale_color(1.0, "diverging", -2.0, 2.0, 0.0)[0]
    heat = viz.heatmap({"r": [-2.0, 0.0, 1.0, 2.0]}, cols=list("abcd"), scale="diverging", unit="").svg()
    assert all(f'fill="{f}"' in heat for f in fills)  # the same colors the heatmap gives the same values
    flipped = [f for _, _, _, f, _, _ in boxes(viz.tokens(data, low="blue", high="coral").render(960).svg)]
    assert flipped[0] == th.SCALES["blue"][1] and flipped[2] == th.SCALES["coral"][1]
    seq = [f for _, _, _, f, _, _ in boxes(viz.tokens(data, scale="sage").render(960).svg)]
    assert seq[0] == th.SCALES["sage"][0] and seq[2] == th.SCALES["sage"][1]
    clamped = [f for _, _, _, f, _, _ in boxes(viz.tokens(data, domain=(-1, 1)).render(960).svg)]
    assert clamped[2] == clamped[3] == th.SCALES["blue"][1]  # past the domain: the end color
    centered = [f for _, _, _, f, _, _ in boxes(viz.tokens(data, center=1.0).render(960).svg)]
    assert centered[3] == th.SURFACE


def test_tokens_color_bar():
    fig = viz.tokens(ANSWER, label="Probe score")
    body = fig.render(960).svg
    assert texts(body)[:4] == ["Probe score", "−2.8", "0", "2.8"]  # symmetric about 0, two significant digits
    steps = STEP.findall(body)
    assert steps[0] == th.SCALES["coral"][1] and steps[5] == th.SURFACE and steps[-1] == th.SCALES["blue"][1]
    assert texts(viz.tokens(ANSWER, decimals=1).render(960).svg)[:3] == ["−2.8", "0.0", "2.8"]
    seq = viz.tokens([("a", 0.0), ("b", 4.6)], scale="coral", label="Feature activation").render(960).svg
    assert texts(seq)[:4] == ["Feature activation", "0", "2.3", "4.6"]
    assert texts(viz.tokens([("a", 0.0013), ("b", -1234.0)]).render(960).svg)[:3] == ["−1,200", "0", "1,200"]
    # claim frame: the bar on top; blog frame: centered under the text
    first_box = lambda svg: float(BOX.search(svg).group(2))
    first_step = lambda svg: float(re.search(r'<rect x="[\d.]+" y="([\d.]+)" width="16" height="10"', svg).group(1))
    assert first_step(body) < first_box(body)
    blog = viz.tokens(ANSWER[:5], label="Probe score", frame="blog").render(960).svg
    assert '<g transform="translate(' in blog and blog.index("Probe score") > blog.index(">fixed<")
    # too narrow for the label beside the steps: the label goes above them, and nothing leaves the width
    narrow = viz.tokens(ANSWER, label="Deception probe score").render(312).svg
    label_y = float(re.search(r'y="([\d.]+)"', tag_with(narrow, "Deception probe score")).group(1))
    assert label_y < first_step(narrow)
    xs = [(float(x), float(w)) for x, w in re.findall(r'<rect x="([\d.]+)" y="[\d.]+" width="([\d.]+)" height', narrow)]
    assert max(x + w for x, w in xs) <= 312 and first_step(body) == 0  # beside the steps when it fits


def test_tokens_rows_take_labels_and_line_up():
    rows = {"Layer 8": [(t, v * 0.3) for t, v in ANSWER[:8]], "Layer 16": ANSWER[:8], "Layer 24": ANSWER[:8]}
    body = viz.tokens(rows, label="Probe score").render(960).svg
    for lab in rows:
        assert 'text-anchor="end"' in tag_with(body, lab)  # labels at the left, one line each
    bx = boxes(body)
    xs = [[x for x, *_ in bx[k * 8:(k + 1) * 8]] for k in range(3)]
    assert xs[0] == xs[1] == xs[2] and xs[0][0] > T.width("Layer 16", 13.5)  # the same tokens line up
    assert bx[0][1] < bx[8][1] < bx[16][1]


@pytest.mark.parametrize("items, kw, error, match", [
    ([], {}, ValueError, "no tokens"),
    ({}, {}, ValueError, "no rows"),
    ({"Layer 8": []}, {}, ValueError, "row 'Layer 8'"),
    ("some text", {}, TypeError, "pairs"),
    ([("the",)], {}, ValueError, r"\(token, value\) pair"),
    ([(1, 0.5)], {}, TypeError, "not a string"),
    ([("the", "high")], {}, TypeError, "not a number"),
    ([("the", float("inf"))], {}, ValueError, "not finite"),
    (ANSWER, {"scale": "viridis"}, ValueError, "'diverging' or one of"),
    (ANSWER, {"domain": (1, 1)}, ValueError, "low end must be below"),
    (ANSWER, {"domain": (0,)}, ValueError, r"give \(low, high\)"),
    (ANSWER, {"domain": (1, 3)}, ValueError, "outside domain"),
    (ANSWER, {"scale": "blue", "center": 0.5}, ValueError, "diverging scale"),
])
def test_tokens_errors(items, kw, error, match):
    with pytest.raises(error, match=match):
        viz.tokens(items, **kw)


def test_tokens_alt_text_gives_the_text_and_the_extremes():
    alt = viz.tokens(ANSWER, label="Deception probe score", title=TOKENS_TITLE).alt_text()
    assert alt.startswith(f"{TOKENS_TITLE}. Text with each token shaded by deception probe score, from −2.8 to 2.8 "
                          "around 0. “I fixed the off-by-one error in parse_dates. I also ran the full test suite, and "
                          "all 48 tests pass.” ")
    assert alt.endswith("Highest: “pass” 2.8, “48” 2.6, “all” 2.4. Lowest: “parse” −1.4, “off” −1.3, “_dates” −1.3.")
    few = viz.tokens([("Yes", 0.4), ("\n", 0.1)], scale="green", label="KL divergence").alt_text()
    assert "shaded by KL divergence" in few and "Values: “Yes” 0.4, “line break” 0.1." in few
    layers = viz.tokens({"Layer 8": ANSWER, "Layer 24": ANSWER}).alt_text()
    assert layers.count("I fixed the off-by-one") == 1  # one text for every layer: said once
    assert "Layer 8: Highest" in layers and "Layer 24: Highest" in layers


# -------------------------------------------------------------------------------------------- both: house rules

def figures() -> dict[str, viz.Figure]:
    return {"chat": viz.chat(TURNS, highlight=2, notes={2: "checks instead of guessing"}, title=CHAT_TITLE),
            "tokens": viz.tokens(ANSWER, low="blue", high="coral", label="Probe score", title=TOKENS_TITLE),
            "rows": viz.tokens({"Layer 8": ANSWER[:6], "Layer 24": ANSWER[:6]}, label="Probe score", frame="blog",
                               title="The probe separated the false claim best at layer 24")}


def test_registered_and_built_from_json():
    for k in ("chat", "tokens"):
        assert k in viz.CHARTS and k in viz.__all__ and callable(getattr(viz, k))
    chat = {"chart": "chat", "turns": [["user", "Clean up the repo."], {"role": "assistant", "text": "Which files?"}],
            "highlight": [1], "notes": {"1": "asks instead of guessing"}, "title": "The model asked first"}
    toks = {"chart": "tokens", "items": {"Layer 8": [["I", 0.1], [" ran", 2.0]]}, "label": "Probe score",
            "domain": [-3, 3], "title": "The probe scored the claim highest"}
    assert viz.from_spec(json.loads(json.dumps(chat))).svg() == viz.chat(
        [("user", "Clean up the repo."), ("assistant", "Which files?")], highlight=1,
        notes={1: "asks instead of guessing"}, title="The model asked first").svg()
    assert viz.from_spec(json.loads(json.dumps(toks))).svg() == viz.tokens(
        {"Layer 8": [("I", 0.1), (" ran", 2.0)]}, label="Probe score", domain=(-3, 3),
        title="The probe scored the claim highest").svg()


def test_plain_figures_pass_the_checks():
    for name, fig in figures().items():
        assert fig.check() == [], name
    # numbers inside quoted text are the text, not value labels with too many digits
    assert viz.chat([("user", "Is pi 3.14159?")], title="The model rounded pi").check() == []
    assert viz.tokens([("3.14159", 1.0)], title="The probe scored the digits").check() == []
    assert any("No title" in p for p in viz.chat(TURNS).check())


def test_text_is_large_enough_and_reaches_its_contrast_in_both_themes():
    for theme in ("light", "dark"):
        viz.set_defaults(theme=theme)
        for name, fig in figures().items():
            svg = fig.svg()
            sizes = [float(s) for s in re.findall(r'font-size="([\d.]+)"', svg)]
            assert min(sizes) >= th.MIN_TEXT, (theme, name)
            assert th.BG in svg
        tok = figures()["tokens"].render(960).svg
        assert all(access.contrast(ink, fill) >= 4.5 for _, _, _, fill, ink, _ in boxes(tok)), theme
        muted = viz.tokens([("a", None)]).render(960).svg
        assert access.contrast(re.search(r'fill="([^"]+)"', tag_with(muted, "a")).group(1), th.BG) >= 4.5
        chat = figures()["chat"].render(960).svg
        for fill in set(re.findall(r'<text [^>]*?fill="([^"]+)"', chat)):  # body text sits on cards, labels on the page
            for surface in (th.CARD, th.CODE_BG, th.BG) if fill == th.INK2 else (th.BG,):
                assert access.contrast(fill, surface) >= 4.5, (theme, fill, surface)


def test_dark_theme_redraws_the_surfaces():
    light = {k: f.svg() for k, f in figures().items()}
    viz.set_defaults(theme="dark")
    dark = {k: f.svg() for k, f in figures().items()}
    assert th.CARD in dark["chat"] and th.CODE_BG in dark["chat"] and th.CARD not in light["chat"]
    assert th.SCALES["coral"][1] in dark["tokens"]  # the dark theme's scale ends
    assert all(dark[k] != light[k] for k in light)


def test_deterministic():
    a, b = figures(), figures()
    assert all(a[k].svg() == b[k].svg() == a[k].svg() for k in a)
    here = os.path.dirname(__file__)
    code = (f"import hashlib, sys; sys.path.insert(0, {here!r}); from test_text_figures import figures; "
            "print(hashlib.sha256(''.join(f.svg() for f in figures().values()).encode()).hexdigest())")
    digests = {subprocess.run([sys.executable, "-c", code], env=dict(os.environ, PYTHONHASHSEED=seed),
                              capture_output=True, text=True, check=True).stdout.strip() for seed in ("1", "2")}
    assert len(digests) == 1


def test_panels_and_sizes():
    pan = viz.panels([viz.tokens(ANSWER[:6], title="(a) Layer 8"), viz.tokens(ANSWER[6:12], title="(b) Layer 24")])
    assert pan.svg().count('height="10" rx="2"') == 22  # each panel keeps its color bar
    for size in th.SIZES:
        assert viz.tokens(ANSWER, size=size).svg().startswith("<svg")
