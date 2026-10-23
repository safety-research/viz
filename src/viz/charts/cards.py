"""Text figures: a prompt with contrasting replies, transcript episodes side by side, a tool definition, a
conversation turn by turn, and text shaded token by token."""
from __future__ import annotations

import math
import operator
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field

from .. import scale as SC
from .. import svg as S
from .. import text as T
from .. import theme as th
from ..colors import ROLES
from ..figure import Body, Figure
from .heatmap import scale_color


def _wrap_mono(s: str, max_w: float, size: float) -> list[str]:
    """Wrap monospace text; very long tokens break anywhere (like overflow-wrap: anywhere)."""
    cw = T.width("0", size, "mono")
    per = max(8, int(max_w * T.SAFETY / cw))
    out: list[str] = []
    for para in s.split("\n"):
        cur = ""
        for w in para.split(" "):
            while len(w) > per:
                if cur:
                    out.append(cur)
                    cur = ""
                out.append(w[:per])
                w = w[per:]
            t = f"{cur} {w}" if cur else w
            if len(t) > per and cur:
                out.append(cur)
                cur = w
            else:
                cur = t
        out.append(cur)
    return out


def _accent_card(x, y, w, h, accent: str | None, fill: str, rx: float = 10, top: float = 3, border: str | None = None) -> str:
    """A rounded card; with an accent, a colored top edge that follows the corners (CSS border-top look)."""
    out = [S.rect(x, y, w, h, fill, rx)]
    if accent:  # only the strip above the inner top edge, so no accent shows through along the sides and bottom
        b, n = y + top + rx, S.n
        out.append(S.path(f"M{n(x)},{n(b)} V{n(y + rx)} A{n(rx)},{n(rx)} 0 0 1 {n(x + rx)},{n(y)} H{n(x + w - rx)} "
                          f"A{n(rx)},{n(rx)} 0 0 1 {n(x + w)},{n(y + rx)} V{n(b)} Z M{n(x)},{n(b)} "
                          f"A{n(rx)},{n(rx)} 0 0 1 {n(x + rx)},{n(y + top)} H{n(x + w - rx)} "
                          f"A{n(rx)},{n(rx)} 0 0 1 {n(x + w)},{n(b)} Z", th.color(accent), extra='fill-rule="evenodd"'))
    if border:
        out.append(f'<rect x="{S.n(x + 0.5)}" y="{S.n(y + 0.5)}" width="{S.n(w - 1)}" height="{S.n(h - 1)}" rx="{S.n(rx)}" '
                   f'fill="none" stroke="{border}" stroke-width="1"/>')
    return "".join(out)


# ---------------------------------------------------------------------- prompt + replies

@dataclass
class Reply:
    """One reply card: a bold label, an optional muted note on the right, the quoted text, an accent color."""
    label: str
    text: str
    note: str | None = None
    color: str | None = "gray"


def _reply(r) -> Reply:
    if isinstance(r, Reply):
        return r
    if isinstance(r, Mapping):
        return Reply(**r)
    return Reply(*r)


def quotes(replies, *, prompt=None, prompt_label="The person", prompt_note=None, cols=None, text_size=16,
           title=None, subtitle=None, frame=None, width=None) -> Figure:
    """A message and the replies to it, side by side (e.g. the same refusal for different reasons).

    replies: list of Reply(label, text, note, color) or tuples. Text is printed as given; add the quote marks
    and ellipses you want shown. prompt: the message above them (optional).
    """
    reps = [_reply(r) for r in replies]
    ncol = cols or min(len(reps), 3) or 1

    def card(x, y, w, label, note, body, accent, height=None):
        pad_t, pad_x = 14, 18
        lines = T.wrap(body, w - 2 * pad_x, text_size, "serif")
        lh = text_size * 1.5
        h = pad_t + 18 + 8 + lh * len(lines) + 14
        if height:
            h = height
        out = [_accent_card(x, y, w, h, accent, th.CARD)]
        out.append(S.text(x + pad_x, y + pad_t + 14, label, 14, th.INK, weight=600))
        if note:
            out.append(S.text(x + w - pad_x, y + pad_t + 14, note, 13, th.MUTED, "end"))
        b0 = y + pad_t + 18 + 8 + (lh - text_size) / 2 + 0.735 * text_size
        for i, ln in enumerate(lines):
            out.append(S.text(x + pad_x, b0 + i * lh, ln, text_size, th.INK2, family="serif"))
        return "".join(out), h

    def render(W: float) -> Body:
        out, y = [], 0.0
        if prompt:
            svg_, h = card(0, 0, W, prompt_label, prompt_note, prompt, None)
            out.append(svg_)
            y = h + 14
        gap = 14
        cw = (W - gap * (ncol - 1)) / ncol
        for start in range(0, len(reps), ncol):
            row = reps[start:start + ncol]
            hs = [card(0, 0, cw, r.label, r.note, r.text, r.color)[1] for r in row]
            hmax = max(hs)
            for k, r in enumerate(row):
                svg_, _ = card(k * (cw + gap), y, cw, r.label, r.note, r.text, r.color, hmax)
                out.append(svg_)
            y += hmax + gap
        return Body("".join(out), y - gap + 2)

    return Figure(render, title=title, subtitle=subtitle, legend=False, frame=frame, width=width,
                  kind="quotes")


# ---------------------------------------------------------------------- transcript episodes

@dataclass
class Episode:
    """One transcript card. blocks: (label, kind, text) with kind "quote" (italic serif with a rule),
    "code" (monospace on a panel) or "text"; outcome: ("Paused for a person", "blue")."""
    title: str
    blocks: Sequence[tuple[str, str, str]] = field(default_factory=list)
    meta: str | None = None
    outcome: tuple[str, str] | None = None


def _episode(e) -> Episode:
    if isinstance(e, Episode):
        return e
    if isinstance(e, Mapping):
        return Episode(**e)
    return Episode(*e)


def episodes(items, *, cols=2, title=None, subtitle=None, frame=None, width=None) -> Figure:
    """Transcript excerpts side by side (the same model on the same task, without and with an intervention)."""
    eps = [_episode(e) for e in items]
    ncol = max(1, min(cols, len(eps)))

    def layout(e: Episode, w: float, x: float, y: float, height: float | None = None):
        px, pt = 20, 18
        inner = w - 2 * px
        out, yy = [], y + pt
        # header: title left, meta right (wraps under the title when both don't fit)
        tw = T.width(e.title, 14, "sans", 600)
        mw = T.width(e.meta, 12) if e.meta else 0
        hdr = [S.text(x + px, yy + 14, e.title, 14, th.INK, weight=600)]
        if e.meta and tw + 10 + mw <= inner:
            hdr.append(S.text(x + w - px, yy + 14, e.meta, 12, th.MUTED, "end"))
            yy += 19
        elif e.meta:
            yy += 19
            for ln in T.wrap(e.meta, inner, 12):
                hdr.append(S.text(x + px, yy + 12, ln, 12, th.MUTED))
                yy += 16
        else:
            yy += 19
        out += hdr
        for label, kind, body in e.blocks:
            yy += 12
            if label:
                out.append(S.text(x + px, yy + 10, label.upper(), th.MIN_TEXT, th.MUTED, letter_spacing=0.66))
                yy += 14 + 4
            if kind == "quote":
                size, lh = 15, 22.5
                lines = T.wrap(body, inner - 14, size, "serif", italic=True)
                out.append(S.rect(x + px, yy + 2, 2, lh * len(lines) - 4, th.AXIS))
                for i, ln in enumerate(lines):
                    out.append(S.text(x + px + 14, yy + (lh - size) / 2 + 0.735 * size + i * lh, ln, size, th.INK,
                                      family="serif", italic=True))
                yy += lh * len(lines)
            elif kind == "code":
                size, lh = 12.5, 12.5 * 1.55
                lines = _wrap_mono(body, inner - 24, size)
                h = 20 + lh * len(lines)
                out.append(S.rect(x + px, yy, inner, h, th.CODE_BG, 6))
                for i, ln in enumerate(lines):
                    out.append(S.text(x + px + 12, yy + 10 + (lh - size) / 2 + 0.8 * size + i * lh, ln, size, th.INK2,
                                      family="mono", extra='xml:space="preserve"'))
                yy += h
            else:
                size, lh = 13.5, 13.5 * 1.5
                lines = T.wrap(body, inner, size)
                for i, ln in enumerate(lines):
                    out.append(S.text(x + px, yy + (lh - size) / 2 + 0.992 * size + i * lh - 1, ln, size, th.INK2))
                yy += lh * len(lines)
        if e.outcome:
            yy += 12
            text_, col = e.outcome
            out.append(S.circle(x + px + 5, yy + 8, 5, th.color(col)))
            out.append(S.text(x + px + 18, yy + 12.5, text_, 12.5, th.INK, weight=600))
            yy += 17
        h = (yy - y) + pt
        if height:
            h = height
        card = _accent_card(x, y, w, h, None, th.EP_CARD, 10, border=th.RULE)
        return card + "".join(out), h

    def render(W: float) -> Body:
        gap = 18
        cw = (W - gap * (ncol - 1)) / ncol
        out, y = [], 0.0
        for start in range(0, len(eps), ncol):
            row = eps[start:start + ncol]
            hmax = max(layout(e, cw, 0, 0)[1] for e in row)
            for k, e in enumerate(row):
                out.append(layout(e, cw, k * (cw + gap), y, hmax)[0])
            y += hmax + gap
        return Body("".join(out), y - gap + 2)

    return Figure(render, title=title, subtitle=subtitle, legend=False, frame=frame, width=width,
                  kind="episodes")


# ---------------------------------------------------------------------- tool definition

def code_card(name: str, params: Mapping[str, str] | None = None, description: str = "", *, accent="intervention",
              title=None, subtitle=None, frame=None, width=None) -> Figure:
    """A tool or function definition: the signature in monospace, then its description in serif.
    params: {"reason": "What you'd like to discuss."} prints as reason: "What you'd like to discuss."."""
    params = dict(params or {})
    SIG, DESC = 21, 20

    def render(W: float) -> Body:
        px, pt, pb = 34, 26, 28
        inner = W - 2 * px
        fn_c, punct = th.INK, th.MUTED
        par_c, str_c = th.readable("deep-blue", th.CARD_LIGHT), th.readable("clay", th.CARD_LIGHT)
        pieces = [[(name, fn_c, 600), ("(", punct, 400)]]
        items = list(params.items())
        one_line = name + "(" + ", ".join(f'{k}: "{v}"' for k, v in items) + ")"
        multiline = T.width(one_line, SIG, "mono") > inner
        for i, (k, v) in enumerate(items):
            seg = [(k, par_c, 400), (": ", punct, 400), (f'"{v}"', str_c, 400)]
            if i < len(items) - 1:
                seg.append((",", punct, 400))
            if multiline:
                pieces.append([("    ", punct, 400)] + seg)
            else:
                if i:
                    pieces[-1].append((" ", punct, 400))
                pieces[-1] += seg
        if multiline:
            pieces.append([(")", punct, 400)])
        else:
            pieces[-1].append((")", punct, 400))
        out = []
        y = pt + 4
        sig_lh = SIG * 1.35
        for ln in pieces:
            parts = [(t, {"size": SIG, "fill": c, "weight": w, "family": "mono"}) for t, c, w in ln]
            out.append(S.spans(px, y + 0.82 * SIG, parts, base_family="mono"))
            y += sig_lh
        if description:
            y += 18 - (sig_lh - SIG)
            lh = DESC * 1.62
            lines = T.wrap(description, inner, DESC, "serif")
            for i, ln in enumerate(lines):
                out.append(S.text(px, y + (lh - DESC) / 2 + 0.735 * DESC + i * lh, ln, DESC, th.mix(th.INK, th.INK2, 0.5), family="serif"))
            y += lh * len(lines)
        h = y + pb
        # CSS look: a 4px accent top edge, 1px rule on the other sides
        card = (S.rect(0, 0, W, h, th.color(accent), 14) + S.rect(0, 4, W, h - 4, th.RULE, 14) +
                S.rect(1, 5, W - 2, h - 6, th.CARD_LIGHT, 13))
        return Body(card + "".join(out), h + 2)

    return Figure(render, title=title, subtitle=subtitle, legend=False, frame=frame, width=width,
                  kind="code_card")


# ---------------------------------------------------------------------- conversation

ROLE_LABELS = {"user": "User", "assistant": "Assistant", "system": "System", "tool_call": "Tool call",
               "tool_result": "Tool result"}


def _turn(t) -> tuple[str, str]:
    """One turn as (role, text), from (role, text) or {"role": ..., "text": ...}; "content" works for "text", as in
    API message lists."""
    if isinstance(t, Mapping):
        if "role" not in t or ("text" not in t and "content" not in t):
            raise ValueError(f"a chat turn needs a role and a text, not {dict(t)!r}")
        role, text = t["role"], t["text"] if "text" in t else t["content"]
    elif isinstance(t, Sequence) and not isinstance(t, str) and len(t) == 2:
        role, text = t
    else:
        raise ValueError(f"a chat turn is (role, text) or {{'role': ..., 'text': ...}}, not {t!r}")
    key = str(role).strip().lower().replace(" ", "_").replace("-", "_")
    if key not in ROLE_LABELS:
        raise ValueError(f"unknown chat role {role!r}; use one of: {', '.join(ROLE_LABELS)}")
    if not isinstance(text, str):
        raise TypeError(f"the text of a chat turn is a string, not {type(text).__name__}")
    return key, text


def _turns(turns) -> list[tuple[str, str]]:
    if isinstance(turns, (str, Mapping)) or not isinstance(turns, Iterable):
        raise TypeError("chat takes a list of turns: [(role, text), ...]")
    out = [_turn(t) for t in turns]
    if not out:
        raise ValueError("chat needs at least one turn")
    return out


def _turn_index(i, n: int, what: str) -> int:
    """A turn's position from its index: negative counts from the end, and a JSON key "2" means 2."""
    if isinstance(i, str) and i.strip().removeprefix("-").isdigit():
        i = int(i)
    try:
        if isinstance(i, bool):
            raise TypeError
        k = operator.index(i)
    except TypeError:
        raise TypeError(f"{what}: {i!r} is not a turn index") from None
    if not -n <= k < n:
        raise ValueError(f"{what}: there is no turn {k} in {n} turns")
    return k % n


def _highlights(highlight, n: int) -> set[int]:
    if highlight is None:
        return set()
    if isinstance(highlight, str) or not isinstance(highlight, Iterable):  # one index
        highlight = [highlight]
    return {_turn_index(i, n, "highlight") for i in highlight}


def _turn_notes(notes, n: int) -> dict[int, str]:
    if notes is None:
        return {}
    if not isinstance(notes, Mapping):
        raise TypeError("notes: {turn index: 'short note'}")
    return {_turn_index(k, n, "notes"): str(v) for k, v in notes.items()}


def _wrap_serif(s: str, max_w: float, size: float) -> list[str]:
    """Word wrap that also breaks a word longer than the line, such as a URL, between characters."""
    limit = max_w * T.SAFETY
    out: list[str] = []
    for ln in T.wrap(s.replace("\r\n", "\n").expandtabs(4), max_w, size, "serif"):
        while len(ln) > 1 and T.width(ln, size, "serif") > limit:
            lo, hi = 1, len(ln) - 1  # the longest start of the word that fits
            while lo < hi:
                mid = (lo + hi + 1) // 2
                lo, hi = (mid, hi) if T.width(ln[:mid], size, "serif") <= limit else (lo, mid - 1)
            out.append(ln[:lo])
            ln = ln[lo:]
        out.append(ln)
    return out


def _wrap_code(s: str, max_w: float, size: float) -> list[str]:
    """Monospace wrap that keeps each line's indentation, so code and JSON stay readable."""
    cw = T.width("0", size, "mono")
    out: list[str] = []
    for para in s.replace("\r\n", "\n").expandtabs(4).split("\n"):
        body = para.lstrip(" ")
        indent = " " * min(len(para) - len(body), int(max_w / cw) // 2)  # deep indentation still leaves room
        out += [indent + ln for ln in _wrap_mono(body, max_w - len(indent) * cw, size)]
    return out


def _edge_card(x, y, w, h, fill: str, rx: float, accent: str | None = None, edge: float = 3) -> str:
    """A rounded card; with an accent, a colored left edge that follows the corners (CSS border-left look). The edge
    is drawn over the card's left strip only, so no colored hairline shows around the card's other sides."""
    card = S.rect(x, y, w, h, fill, rx)
    if not accent:
        return card
    r = min(rx, w / 2, h / 2)
    e = min(edge, r)
    dy = r - math.sqrt(r * r - (r - e) ** 2)  # where the edge's inner side meets the corner arcs
    d = (f"M{S.n(x + e)},{S.n(y + dy)} A{S.n(r)},{S.n(r)} 0 0 0 {S.n(x)},{S.n(y + r)} V{S.n(y + h - r)} "
         f"A{S.n(r)},{S.n(r)} 0 0 0 {S.n(x + e)},{S.n(y + h - dy)} Z")
    return card + S.path(d, accent)


def chat(turns, *, highlight=None, notes=None, title=None, subtitle=None, frame=None, width=None) -> Figure:
    """A conversation turn by turn, as write-ups show it: each turn under a small uppercase label, user and system
    turns on a card, assistant turns as serif text with a thin rule at the left, tool calls and results in monospace.

    turns: [(role, text), ...] or [{"role": ..., "text": ...}, ...]; the roles are user, assistant, system, tool_call
    and tool_result, in any case. Text prints as given: add the quote marks and the "…" for cuts you want shown.
    highlight: a turn index or a list of them; those turns take the intervention color for their rule and label.
    notes: {turn index: "asks instead of guessing"}, printed muted beside that turn's label. Negative indices count
    from the end.
    """
    ts = _turns(turns)
    marked, noted = _highlights(highlight, len(ts)), _turn_notes(notes, len(ts))
    SIZE, LH = 15, 22.5             # user, system and assistant text (serif)
    CODE, CLH = 12.5, 12.5 * 1.55   # tool calls and results (mono)
    PX, PY, CPY = 16, 12, 10        # text inset from the left; card and panel padding
    NOTE, GAP = 13, 16

    def render(W: float) -> Body:
        accent = th.color(ROLES["intervention"])
        out, y = [], 0.0
        for i, (role, text) in enumerate(ts):
            on = i in marked
            if i:
                y += GAP
            label = ROLE_LABELS[role].upper()
            out.append(S.text(0, y + 10, label, th.MIN_TEXT, th.readable(accent, th.BG) if on else th.MUTED,
                              letter_spacing=0.66))
            head = 14
            if i in noted:  # beside the label, wrapping under itself when it runs long
                nx = T.width(label, th.MIN_TEXT, letter_spacing=0.66) + 10
                for k, ln in enumerate(T.wrap(noted[i], max(W - nx, 60), NOTE)):
                    out.append(S.text(nx, y + 10 + k * 17, ln, NOTE, th.MUTED))
                    head = 14 + k * 17
            y += head + 4
            if role == "assistant":
                lines = _wrap_serif(text, W - PX, SIZE)
                h = LH * len(lines)
                out.append(S.rect(0, y + 2, 3 if on else 2, h - 4, accent if on else th.AXIS))
                b0 = y + T.baseline(SIZE, "serif", LH)
                out += [S.text(PX, b0 + k * LH, ln, SIZE, th.INK2, family="serif")
                        for k, ln in enumerate(lines) if ln.strip()]
            elif role in ("user", "system"):
                lines = _wrap_serif(text, W - 2 * PX, SIZE)
                h = 2 * PY + LH * len(lines)
                out.append(_edge_card(0, y, W, h, th.CARD, 8, accent if on else None))
                b0 = y + PY + T.baseline(SIZE, "serif", LH)
                out += [S.text(PX, b0 + k * LH, ln, SIZE, th.INK2, family="serif")
                        for k, ln in enumerate(lines) if ln.strip()]
            else:  # tool_call, tool_result
                lines = _wrap_code(text, W - 2 * PX, CODE)
                h = 2 * CPY + CLH * len(lines)
                out.append(_edge_card(0, y, W, h, th.CODE_BG, 6, accent if on else None))
                b0 = y + CPY + (CLH - CODE) / 2 + 0.8 * CODE
                out += [S.text(PX, b0 + k * CLH, ln, CODE, th.INK2, family="mono", extra='xml:space="preserve"')
                        for k, ln in enumerate(lines) if ln.strip()]
            y += h
        return Body("".join(out), y + 2)

    return Figure(render, title=title, subtitle=subtitle, legend=False, frame=frame, width=width, kind="chat")


# ---------------------------------------------------------------------- tokens shaded by value

def _token_pairs(seq, row=None) -> list[tuple[str, float | None]]:
    what = "tokens" if row is None else f"tokens, row {row!r}"
    if isinstance(seq, (str, Mapping)) or not isinstance(seq, Iterable):
        raise TypeError(f"{what}: give a list of (token, value) pairs")
    out = []
    for p in seq:
        if isinstance(p, str) or not isinstance(p, Sequence) or len(p) != 2:
            raise ValueError(f"{what}: each item is a (token, value) pair, not {p!r}")
        tok, v = p
        if not isinstance(tok, str):
            raise TypeError(f"{what}: the token {tok!r} is not a string")
        if v is not None:
            try:
                v = float(v)
            except (TypeError, ValueError):
                raise TypeError(f"{what}: the value of {tok!r} is not a number: {v!r}") from None
            if math.isinf(v):
                raise ValueError(f"{what}: the value of {tok!r} is not finite")
            v = None if math.isnan(v) else v
        out.append((tok, v))
    if not out:
        raise ValueError(f"{what}: no tokens")
    return out


def _token_rows(items) -> list[tuple[str | None, list[tuple[str, float | None]]]]:
    """[(row label, [(token, value), ...]), ...]: one unlabeled row from a list of pairs, or a labeled row for each
    key of a {row label: pairs} mapping."""
    if isinstance(items, Mapping):
        if not items:
            raise ValueError("tokens: no rows")
        return [(str(k), _token_pairs(v, k)) for k, v in items.items()]
    return [(None, _token_pairs(items))]


def _token_scale(rows, scale, domain, center) -> tuple[float, float, float | None]:
    """(low end, high end, center or None): the given domain, else the values' range. A diverging scale is centered
    (at 0 by default) and reaches as far below the center as above it."""
    if scale != "diverging" and scale not in th.SCALES:
        raise ValueError(f"scale={scale!r}: use 'diverging' or one of: {', '.join(th.SCALES)}")
    if center is not None and scale != "diverging":
        raise ValueError("center= sets the middle of the diverging scale; a sequential scale has none")
    c = (0.0 if center is None else float(center)) if scale == "diverging" else None
    vals = [v for _, row in rows for _, v in row if v is not None]
    if domain is not None:
        try:
            lo, hi = (float(x) for x in domain)
        except (TypeError, ValueError):
            raise ValueError(f"domain={domain!r}: give (low, high)") from None
        if not lo < hi:
            raise ValueError(f"domain={domain!r}: the low end must be below the high end")
        if c is not None and not lo <= c <= hi:
            raise ValueError(f"center={c:g} lies outside domain={domain!r}")
        return lo, hi, c
    if c is not None:
        span = max((abs(v - c) for v in vals), default=0.0) or 1.0
        return c - span, c + span, c
    lo, hi = (min(vals), max(vals)) if vals else (0.0, 1.0)
    return lo, (hi if hi > lo else lo + 1), None


def _sig2(v: float) -> str:
    """Two significant digits without trailing zeros: 2.37 -> 2.4, 0.873 -> 0.87, 1234 -> 1,200, -1.0 -> −1."""
    if v == 0:
        return "0"
    d = 1 - math.floor(math.log10(abs(v)))
    s = SC.fmt_num(round(v, d), max(d, 0))
    return s.rstrip("0").rstrip(".") if "." in s else s


def _token_fmt(decimals):
    """The color bar's number format: two significant digits, or a fixed number of decimals."""
    return _sig2 if decimals is None else (lambda v: SC.fmt_num(v, decimals))


def _colorbar(lo: float, hi: float, mid: float, fill, label: str | None, fmt, W: float) -> tuple[str, float, float]:
    """A stepped color bar: the label, eleven steps from lo to hi, and the low, middle and high values under them.
    The label goes above the steps when both don't fit in the width W. Returns (svg, width, height)."""
    n, sw, sh, g = 11, 16, 10, 1
    pos = lambda v: bx + sw / 2 + (v - lo) / (hi - lo) * (n - 1) * (sw + g)
    tick_w = lambda v: T.width(fmt(v), th.TICK_SIZE)
    lab_w = T.width(label, th.LEGEND_SIZE) if label else 0.0
    above = bool(label) and lab_w + 10 + n * (sw + g) > W
    if above:
        out = [S.text(0, T.baseline(th.LEGEND_SIZE), label, th.LEGEND_SIZE, th.INK2)]
        by = T.line_height(th.LEGEND_SIZE) + 4
    else:
        out = [S.text(0, sh / 2 + 4.5, label, th.LEGEND_SIZE, th.INK2)] if label else []
        by = 0.0
    bx = max(0.0 if above or not label else lab_w + 10, tick_w(lo) / 2 - sw / 2)  # the low value stays inside
    out += [S.rect(bx + k * (sw + g), by, sw, sh, fill(lo + k * (hi - lo) / (n - 1)), 2) for k in range(n)]
    ticks = [lo, hi]
    if all(abs(pos(mid) - pos(e)) > (tick_w(mid) + tick_w(e)) / 2 + 6 for e in (lo, hi)):  # room for the middle
        ticks.insert(1, mid)
    out += [S.text(pos(v), by + sh + 15, fmt(v), th.TICK_SIZE, th.MUTED, "middle") for v in ticks]
    right = max(bx + n * (sw + g) - g, pos(hi) + tick_w(hi) / 2, lab_w if above else 0.0)
    return "".join(out), right, by + sh + 19


def _return_arrow(x: float, y: float, h: float, ink: str) -> str:
    """A small return arrow, drawn rather than typed: the bundled fonts have no glyph for it."""
    mid = y + h * 0.6
    d = (f"M{S.n(x + 9.5)},{S.n(y + h * 0.3)} V{S.n(mid)} H{S.n(x + 4.5)} "
         f"M{S.n(x + 7)},{S.n(mid - 2.5)} L{S.n(x + 4.5)},{S.n(mid)} L{S.n(x + 7)},{S.n(mid + 2.5)}")
    return S.path(d, "none", ink, 1.3, extra='stroke-linecap="round" stroke-linejoin="round"')


def tokens(items, *, scale="diverging", domain=None, center=None, low="coral", high="blue", label=None,
           decimals=None, title=None, subtitle=None, frame=None, width=None) -> Figure:
    """Text with each token's background shaded by a value, such as a probe score, an attribution or a steering
    effect, and a stepped color bar as the key.

    items: [(token, value), ...] with the tokens as the tokenizer gives them (" the" keeps its space, and "\\n"
    breaks the line), or {row label: [(token, value), ...]} for several rows, such as layers, each labeled at the
    left. Lines wrap between tokens, never inside one. A token whose value is None prints muted, without a box.
    scale: "diverging" (the default: `low`, coral, below the center and `high`, blue, above it; pass low="blue",
    high="coral" when higher is worse) or a sequential scale, "blue", "coral", "sage" or "green", as in heatmap.
    domain: (low, high), the values at the two ends of the colors. By default the values' range, and for a diverging
    scale as far below the center as the farthest value lies from it on either side. center: the diverging scale's
    middle (0). label: what the values are ("Probe score"), written by the color bar. decimals: the color bar's
    values (two significant digits by default).
    """
    rows = _token_rows(items)
    lo, hi, c = _token_scale(rows, scale, domain, center)
    fmt = _token_fmt(decimals)
    FAM, SIZE = "serif", 16
    BOX, PAD, GAP, RX, LINE_GAP, ROW_GAP, LABEL = 24, 2, 1, 3, 5, 10, 13.5

    def fill_of(v: float) -> str:
        return scale_color(v, scale, lo, hi, c, low, high)[0]

    def flow(row, x0: float, x1: float, top: float) -> tuple[list[str], float, float]:
        """One row's tokens from x0 to x1, wrapping only between tokens. Returns the SVG pieces, their height and the
        right end of the longest line."""
        out: list[str] = []
        space, base = T.width(" ", SIZE, FAM), T.baseline(SIZE, FAM, BOX)
        x, line, last, right = x0, 0, 0, x0

        def place(w: float, lead: float) -> tuple[float, float]:
            """Where a box w wide goes after `lead` px of spaces: on this line if it fits, else at the next start."""
            nonlocal x, line, last, right
            if x > x0 and x + lead + w > x1:
                line, x, lead = line + 1, x0, 0.0
            bx, last = x + lead, line
            x, right = bx + w + GAP, max(right, bx + w)
            return bx, top + line * (BOX + LINE_GAP)

        for tok, v in row:
            fill = None if v is None else fill_of(v)
            ink = th.MUTED if fill is None else th.text_on(fill)
            pieces = tok.replace("\r\n", "\n").expandtabs(4).split("\n")
            if not any(p.strip() for p in pieces):  # only spaces and line breaks
                if len(pieces) == 1:  # spaces: a box as wide as they are, so their value shows
                    if fill is None:
                        x += space * len(tok)
                    else:
                        w = max(space * len(tok), 6.0)
                        bx, by = place(w, 0.0)
                        out.append(S.rect(bx, by, w, BOX, fill, RX))
                    continue
                if fill is not None:  # a line break: a box with a return arrow, then the break
                    bx, by = place(14.0, 0.0)
                    out.append(S.rect(bx, by, 14, BOX, fill, RX) + _return_arrow(bx, by, BOX, ink))
                line, x = line + len(pieces) - 1, x0 + space * len(pieces[-1])
                continue
            for k, p in enumerate(pieces):
                if k:  # a line break inside the token
                    line, x = line + 1, x0
                core = p.strip(" ")
                if not core:
                    continue
                w = T.width(core, SIZE, FAM) + 2 * PAD
                bx, by = place(w, space * (len(p) - len(p.lstrip(" "))))
                if fill is not None:
                    out.append(S.rect(bx, by, w, BOX, fill, RX))
                out.append(S.text(bx + PAD, by + base, core, SIZE, ink, family=FAM, extra='xml:space="preserve"'))
                x += space * (len(p) - len(p.rstrip(" ")))
        return out, (last + 1) * (BOX + LINE_GAP) - LINE_GAP, right

    def render(W: float) -> Body:
        named = [lab for lab, _ in rows if lab is not None]
        col = min(max(T.width(lab, LABEL) for lab in named), 0.3 * W) if named else 0.0  # row labels, at most 30%
        L = col + 14 if named else 0.0
        bar, bar_w, bar_h = _colorbar(lo, hi, (lo + hi) / 2 if c is None else c, fill_of, label, fmt, W)
        claim = fig._frame() == "claim"  # the color bar goes where the frame puts legends: on top, or centered below
        body, y, block = [], (bar_h + 16 if claim else 0.0), L
        for r, (lab, row) in enumerate(rows):
            if r:
                y += ROW_GAP
            pieces, h, right = flow(row, L, W, y)
            body += pieces
            block = max(block, right)
            if lab is not None:
                lines = T.wrap(lab, col / T.SAFETY + 1, LABEL)  # the widest label fits its column on one line
                body += [S.text(L - 14, y + T.baseline(SIZE, FAM, BOX) + k * 17, ln, LABEL, th.INK2, "end")
                         for k, ln in enumerate(lines)]
                h = max(h, BOX + (len(lines) - 1) * 17)
            y += h
        if claim:
            return Body(bar + "".join(body), y + 2)
        # blog frame: the text block centered under the centered title, the color bar centered below it
        out = S.group("".join(body), (W - block) / 2) + S.group(bar, (W - bar_w) / 2, y + 16)
        return Body(out, y + 16 + bar_h + 2)

    fig = Figure(render, title=title, subtitle=subtitle, legend=False, frame=frame, width=width, kind="tokens")
    return fig
