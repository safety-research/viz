"""Text measurement and wrapping with the same font files Chromium renders with.

Widths come from the vendored variable fonts with the optical-size axis set to the font size, which is what
Chromium does by default (font-optical-sizing: auto). Measured against headless Chromium they agree within
about 2%, enough for label columns and line wrapping (wrapping keeps a small safety margin).
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from PIL import ImageFont, features

from . import theme as th

FONT_DIR = Path(__file__).parent / "fonts"
FILES = {
    ("serif", False): "Newsreader.ttf", ("serif", True): "Newsreader-Italic.ttf",
    ("sans", False): "DMSans.ttf", ("sans", True): "DMSans-Italic.ttf",
    ("mono", False): "JetBrainsMono.ttf", ("mono", True): "JetBrainsMono.ttf",
}
AXES = {"Newsreader.ttf": ("wght", "opsz"), "Newsreader-Italic.ttf": ("wght", "opsz"),
        "DMSans.ttf": ("opsz", "wght"), "DMSans-Italic.ttf": ("opsz", "wght"), "JetBrainsMono.ttf": ("wght",)}
OPSZ = {"Newsreader": (6, 72), "DMSans": (9, 40)}
# ascent (fraction of the em) of each family: places a baseline inside a CSS-style line box
ASCENT = {"serif": 0.735, "sans": 0.992, "mono": 1.02}
DESCENT = {"serif": 0.265, "sans": 0.310, "mono": 0.30}
_REF = 200  # measure at a large size, then scale: avoids hinting/rounding noise at small sizes
_ENGINE = ImageFont.Layout.RAQM if features.check("raqm") else ImageFont.Layout.BASIC
SAFETY = 0.985  # wrap a little early: Chromium snaps glyph advances to whole pixels


@lru_cache(maxsize=256)
def _font(family: str, italic: bool, size: float, weight: int) -> ImageFont.FreeTypeFont:
    name = FILES[(family, italic)]
    f = ImageFont.truetype(str(FONT_DIR / name), _REF, layout_engine=_ENGINE)
    stem = name.split("-")[0].split(".")[0]
    lo, hi = OPSZ.get(stem, (size, size))
    vals = {"opsz": min(max(size, lo), hi), "wght": weight}
    f.set_variation_by_axes([vals[a] for a in AXES[name]])
    return f


def width(s: str, size: float, family: str = "sans", weight: int = 400, italic: bool = False,
          letter_spacing: float = 0.0) -> float:
    """Advance width of `s` in CSS px."""
    if not s:
        return 0.0
    f = _font(th.family(family), italic, round(size * 4) / 4, int(weight))
    return f.getlength(s) * size / _REF + letter_spacing * len(s)


def line_height(size: float, family: str = "sans") -> float:
    """CSS `line-height: normal` for the family (ascent + descent; the fonts have no line gap)."""
    family = th.family(family)
    return size * (ASCENT[family] + DESCENT[family])


def baseline(size: float, family: str = "sans", lh: float | None = None) -> float:
    """Offset from the top of a line box to the baseline, CSS style (half-leading above)."""
    family = th.family(family)
    content = size * (ASCENT[family] + DESCENT[family])
    lh = content if lh is None else lh
    return (lh - content) / 2 + size * ASCENT[family]


def wrap(s: str, max_width: float, size: float, family: str = "sans", weight: int = 400,
         italic: bool = False) -> list[str]:
    """Greedy word wrap; honors explicit newlines. A single word longer than the line stays whole."""
    out: list[str] = []
    limit = max_width * SAFETY
    for para in str(s).split("\n"):
        words = para.split(" ")
        cur = ""
        for w in words:
            t = f"{cur} {w}" if cur else w
            if cur and width(t, size, family, weight, italic) > limit:
                out.append(cur)
                cur = w
            else:
                cur = t
        out.append(cur)
    return out


def wrap_balanced(s: str, max_width: float, size: float, family: str = "sans", weight: int = 400,
                  italic: bool = False) -> list[str]:
    """Wrap into as few lines as greedy wrapping needs, but with lines of even length (no orphan word)."""
    lines = wrap(s, max_width, size, family, weight, italic)
    if len(lines) < 2:
        return lines
    lo = max(width(w, size, family, weight, italic) for w in str(s).split()) / SAFETY
    hi = max_width
    for _ in range(18):
        mid = (lo + hi) / 2
        if len(wrap(s, mid, size, family, weight, italic)) <= len(lines):
            hi = mid
        else:
            lo = mid
    return wrap(s, hi, size, family, weight, italic)


# ---- rich text: **bold**, *italic*, `code`

@dataclass
class Run:
    text: str
    bold: bool = False
    italic: bool = False
    code: bool = False


_TOKEN = re.compile(r"(\*\*.+?\*\*|`[^`]+`|(?<![\w*])\*[^*\s][^*]*?\*(?![\w*]))", re.DOTALL)


def parse(s: str) -> list[Run]:
    """Split mini-markdown into runs."""
    runs: list[Run] = []
    pos = 0
    for m in _TOKEN.finditer(s):
        if m.start() > pos:
            runs.append(Run(s[pos:m.start()]))
        tok = m.group(0)
        if tok.startswith("**"):
            runs.append(Run(tok[2:-2], bold=True))
        elif tok.startswith("`"):
            runs.append(Run(tok[1:-1], code=True))
        else:
            runs.append(Run(tok[1:-1], italic=True))
        pos = m.end()
    if pos < len(s):
        runs.append(Run(s[pos:]))
    return runs


def run_width(r: Run, size: float, family: str, weight: int, bold_weight: int = 600) -> float:
    if r.code:
        return width(r.text, size * 0.86, "mono", 400)
    return width(r.text, size, family, bold_weight if r.bold else weight, r.italic)


def wrap_rich(s: str | list[Run], max_width: float, size: float, family: str = "serif", weight: int = 400,
              bold_weight: int = 600) -> list[list[Run]]:
    """Wrap mixed-style text into lines of runs (spaces kept inside runs)."""
    runs = parse(s) if isinstance(s, str) else s
    rw = lambda r: run_width(r, size, family, weight, bold_weight)
    # break runs into words; a word keeps its style and the space after it. A word that follows another with
    # no space between (a period after `code`) is glued to it, so a line never breaks there.
    tokens: list[list] = []  # [run, starts a paragraph, glued to the previous word]
    pending_space = newpara = False
    for r in runs:
        for p in re.split(r"(\s+)", r.text):
            if not p:
                continue
            if p.isspace():
                newpara = newpara or ("\n" in p)
                pending_space = True
                continue
            glued = bool(tokens) and not pending_space
            lead = ""
            if tokens and pending_space and not newpara:
                prev = tokens[-1][0]
                if prev.code and not r.code:  # keep the space in the proportional font
                    lead = " "
                else:
                    tokens[-1][0] = Run(prev.text + " ", prev.bold, prev.italic, prev.code)
            tokens.append([Run(lead + p, r.bold, r.italic, r.code), newpara, glued])
            pending_space = newpara = False
    units: list[tuple[list[Run], bool]] = []
    for tok, para, glued in tokens:
        if glued and units and not para:
            units[-1][0].append(tok)
        else:
            units.append(([tok], para))
    lines: list[list[Run]] = [[]]
    cur_w = 0.0
    limit = max_width * SAFETY
    for toks, para in units:
        full = sum(rw(t) for t in toks)
        last = toks[-1]
        strip = full - rw(last) + rw(Run(last.text.rstrip(), last.bold, last.italic, last.code))
        if (para and lines[-1]) or (lines[-1] and cur_w + strip > limit):
            lines.append([])
            cur_w = 0.0
        if not lines[-1] and toks[0].text.startswith(" "):
            t0 = toks[0]
            toks = [Run(t0.text.lstrip(), t0.bold, t0.italic, t0.code)] + toks[1:]
            full = sum(rw(t) for t in toks)
        lines[-1].extend(toks)
        cur_w += full
    # merge neighbors with the same style; drop trailing spaces at line ends
    merged: list[list[Run]] = []
    for ln in lines:
        m: list[Run] = []
        for r in ln:
            if m and (m[-1].bold, m[-1].italic, m[-1].code) == (r.bold, r.italic, r.code):
                m[-1] = Run(m[-1].text + r.text, r.bold, r.italic, r.code)
            else:
                m.append(r)
        if m:
            m[-1] = Run(m[-1].text.rstrip(), m[-1].bold, m[-1].italic, m[-1].code)
        merged.append(m)
    return merged
