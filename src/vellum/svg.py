"""Small SVG builders. Everything is a string; coordinates are CSS px."""
from __future__ import annotations

import itertools
import secrets

from . import text as T
from .theme import BG, FAMILIES, INK, INK2

_ids = itertools.count(1)
_prefix = secrets.token_hex(2)


def uid(stem: str = "v") -> str:
    """Unique id, safe when several figures are inlined in one page."""
    return f"{stem}{_prefix}{next(_ids)}"


def esc(s) -> str:
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def n(v: float) -> str:
    """Compact number for attributes."""
    s = f"{v:.2f}"
    return s.rstrip("0").rstrip(".") if "." in s else s


def font_attrs(size: float, family: str = "sans", weight: int = 400, italic: bool = False,
               fill: str = INK2, letter_spacing: float = 0) -> str:
    a = f'font-family="{FAMILIES[family]}" font-size="{n(size)}" fill="{fill}"'
    if weight != 400:
        a += f' font-weight="{weight}"'
    if italic:
        a += ' font-style="italic"'
    if letter_spacing:
        a += f' letter-spacing="{n(letter_spacing)}"'
    if family == "mono":
        a += ' style="font-variant-ligatures:none"'
    return a


def text(x: float, y: float, s, size: float = 13, fill: str = INK2, anchor: str = "start", weight: int = 400,
         family: str = "sans", italic: bool = False, halo: str | None = None, letter_spacing: float = 0,
         extra: str = "") -> str:
    a = font_attrs(size, family, weight, italic, fill, letter_spacing)
    if anchor != "start":
        a += f' text-anchor="{anchor}"'
    if halo:
        a += f' stroke="{halo}" stroke-width="5" stroke-linejoin="round" paint-order="stroke"'
    return f'<text x="{n(x)}" y="{n(y)}" {a}{" " + extra if extra else ""}>{esc(s)}</text>'


def spans(x: float, y: float, parts: list[tuple[str, dict]], anchor: str = "start", halo: str | None = None,
          base_family: str = "sans") -> str:
    """One <text> made of styled tspans: parts = [(string, {size, weight, fill, family, italic, dx}), ...]."""
    out = [f'<text x="{n(x)}" y="{n(y)}" font-family="{FAMILIES[base_family]}" xml:space="preserve"'
           + (' style="font-variant-ligatures:none"' if base_family == "mono" or any(st.get("family") == "mono" for _, st in parts) else "")]
    if anchor != "start":
        out.append(f' text-anchor="{anchor}"')
    if halo:
        out.append(f' stroke="{halo}" stroke-width="5" stroke-linejoin="round" paint-order="stroke"')
    out.append(">")
    for s, st in parts:
        a = [f'font-size="{n(st.get("size", 13))}"', f'fill="{st.get("fill", INK2)}"']
        if st.get("weight", 400) != 400:
            a.append(f'font-weight="{st["weight"]}"')
        if st.get("family") and st["family"] != base_family:
            a.append(f'font-family="{FAMILIES[st["family"]]}"')
        if st.get("italic"):
            a.append('font-style="italic"')
        if st.get("dx"):
            a.append(f'dx="{n(st["dx"])}"')
        out.append(f'<tspan {" ".join(a)}>{esc(s)}</tspan>')
    out.append("</text>")
    return "".join(out)


def rich_lines(x: float, y: float, lines: list[list[T.Run]], size: float, lh: float, family: str = "serif",
               fill: str = INK2, bold_fill: str = INK, weight: int = 400, bold_weight: int = 600,
               anchor: str = "start", code_fill: str | None = None) -> str:
    """Render wrapped rich-text lines; y is the first baseline."""
    out = []
    for i, ln in enumerate(lines):
        if not ln:
            continue
        parts = []
        for r in ln:
            if r.code:
                parts.append((r.text, {"size": size * 0.86, "family": "mono", "fill": code_fill or fill}))
            else:
                parts.append((r.text, {"size": size, "weight": bold_weight if r.bold else weight,
                                       "fill": bold_fill if r.bold else fill, "italic": r.italic, "family": family}))
        out.append(spans(x, y + i * lh, parts, anchor=anchor, base_family=family))
    return "".join(out)


def rect(x: float, y: float, w: float, h: float, fill: str, rx: float = 0, extra: str = "") -> str:
    r = f' rx="{n(rx)}"' if rx else ""
    return f'<rect x="{n(x)}" y="{n(y)}" width="{n(max(w, 0))}" height="{n(max(h, 0))}"{r} fill="{fill}"{" " + extra if extra else ""}/>'


def line(x1: float, y1: float, x2: float, y2: float, stroke: str, width: float = 1, dash: str | None = None,
         cap: str | None = None, extra: str = "") -> str:
    a = f'stroke="{stroke}" stroke-width="{n(width)}"'
    if dash:
        a += f' stroke-dasharray="{dash}"'
    if cap:
        a += f' stroke-linecap="{cap}"'
    return f'<line x1="{n(x1)}" y1="{n(y1)}" x2="{n(x2)}" y2="{n(y2)}" {a}{" " + extra if extra else ""}/>'


def circle(cx: float, cy: float, r: float, fill: str, stroke: str | None = None, sw: float = 0, extra: str = "") -> str:
    s = f' stroke="{stroke}" stroke-width="{n(sw)}"' if stroke else ""
    return f'<circle cx="{n(cx)}" cy="{n(cy)}" r="{n(r)}" fill="{fill}"{s}{" " + extra if extra else ""}/>'


def path(d: str, fill: str = "none", stroke: str | None = None, sw: float = 1, extra: str = "") -> str:
    s = f' stroke="{stroke}" stroke-width="{n(sw)}"' if stroke else ""
    return f'<path d="{d}" fill="{fill}"{s}{" " + extra if extra else ""}/>'


def hbar(x0: float, y: float, x1: float, h: float, fill: str, r: float = 4) -> str:
    """Horizontal bar from x0 (the baseline, square) to x1 (the data end, rounded)."""
    w = abs(x1 - x0)
    if w < 0.5:
        return ""
    r = min(r, w / 2, h / 2)
    if x1 >= x0:
        d = (f"M{n(x0)},{n(y)} h{n(w - r)} a{n(r)},{n(r)} 0 0 1 {n(r)},{n(r)} v{n(h - 2 * r)} "
             f"a{n(r)},{n(r)} 0 0 1 -{n(r)},{n(r)} h-{n(w - r)} z")
    else:
        d = (f"M{n(x0)},{n(y)} h-{n(w - r)} a{n(r)},{n(r)} 0 0 0 -{n(r)},{n(r)} v{n(h - 2 * r)} "
             f"a{n(r)},{n(r)} 0 0 0 {n(r)},{n(r)} h{n(w - r)} z")
    return f'<path d="{d}" fill="{fill}"/>'


def vbar(x: float, y_base: float, y_end: float, w: float, fill: str, r: float = 0) -> str:
    """Vertical bar from the baseline to the data end; square by default (the blog look)."""
    h = abs(y_end - y_base)
    if h < 0.01:
        return ""
    if r <= 0:
        return rect(x, min(y_base, y_end), w, h, fill)
    r = min(r, w / 2, h)
    if y_end <= y_base:  # grows up
        d = (f"M{n(x)},{n(y_base)} v-{n(h - r)} a{n(r)},{n(r)} 0 0 1 {n(r)},-{n(r)} h{n(w - 2 * r)} "
             f"a{n(r)},{n(r)} 0 0 1 {n(r)},{n(r)} v{n(h - r)} z")
    else:
        d = (f"M{n(x)},{n(y_base)} v{n(h - r)} a{n(r)},{n(r)} 0 0 0 {n(r)},{n(r)} h{n(w - 2 * r)} "
             f"a{n(r)},{n(r)} 0 0 0 {n(r)},-{n(r)} v-{n(h - r)} z")
    return f'<path d="{d}" fill="{fill}"/>'


def group(content: str, tx: float = 0, ty: float = 0, extra: str = "") -> str:
    t = f' transform="translate({n(tx)},{n(ty)})"' if (tx or ty) else ""
    return f"<g{t}{' ' + extra if extra else ''}>{content}</g>"


def rotated(x: float, y: float, s, angle: float = -90, size: float = 11.5, fill: str = INK2, anchor: str = "middle",
            weight: int = 400) -> str:
    a = font_attrs(size, "sans", weight, False, fill)
    return (f'<text transform="translate({n(x)},{n(y)}) rotate({n(angle)})" {a} text-anchor="{anchor}">'
            f"{esc(s)}</text>")


def swatch(x: float, y: float, fill: str, size: float = 12, rx: float = 3) -> str:
    return rect(x, y, size, size, fill, rx)


__all__ = [
    "BG",
    "INK",
    "INK2",
    "circle",
    "esc",
    "group",
    "hbar",
    "line",
    "n",
    "path",
    "rect",
    "rich_lines",
    "rotated",
    "spans",
    "swatch",
    "text",
    "uid",
    "vbar",
]
