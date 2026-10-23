"""Text figures: a prompt with contrasting replies, transcript episodes side by side, and a tool definition."""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

from . import svg as S
from . import text as T
from . import theme as th
from .figure import Body, Figure


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
    out = []
    if accent:
        out.append(S.rect(x, y, w, h, th.color(accent), rx))
        out.append(S.rect(x, y + top, w, h - top, fill, rx))
    else:
        out.append(S.rect(x, y, w, h, fill, rx))
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


def quotes(replies, *, prompt=None, prompt_label="The person", prompt_note=None, cols=None, size=16,
           title=None, subtitle=None, frame=None, width=None) -> Figure:
    """A message and the replies to it, side by side (e.g. the same refusal for different reasons).

    replies: list of Reply(label, text, note, color) or tuples. Text is printed as given; add the quote marks
    and ellipses you want shown. prompt: the message above them (optional).
    """
    reps = [_reply(r) for r in replies]
    ncol = cols or min(len(reps), 3) or 1

    def card(x, y, w, label, note, body, accent, height=None):
        pad_t, pad_x = 14, 18
        lines = T.wrap(body, w - 2 * pad_x, size, "serif")
        lh = size * 1.5
        h = pad_t + 18 + 8 + lh * len(lines) + 14
        if height:
            h = height
        out = [_accent_card(x, y, w, h, accent, th.CARD)]
        out.append(S.text(x + pad_x, y + pad_t + 14, label, 14, th.INK, weight=600))
        if note:
            out.append(S.text(x + w - pad_x, y + pad_t + 14, note, 13, th.MUTED, "end"))
        b0 = y + pad_t + 18 + 8 + (lh - size) / 2 + 0.735 * size
        for i, ln in enumerate(lines):
            out.append(S.text(x + pad_x, b0 + i * lh, ln, size, th.INK2, family="serif"))
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

def code_card(name: str, params: Mapping[str, str] | None = None, description: str = "", *, accent="blue",
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
