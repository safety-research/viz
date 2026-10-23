"""The house style's tokens.

The values come from two looks: vertical coral and blue bars in the style of the Anthropic blog, and a clear
style with one claim per figure as a serif title, one accent on the point and direct labels.
"""
from __future__ import annotations

import contextvars
from dataclasses import dataclass


# ---- surfaces and ink
BG = "#FFFFFF"        # figure background: white
CARD = "#F1EEE8"      # quote cards
CARD_LIGHT = "#FFFDF9"  # code / tool cards
SURFACE = "#ECE8E1"   # empty heatmap cell, low end of sequential scales
INK = "#191918"       # titles, emphasized numbers
INK2 = "#3D3C38"      # labels, body text
MUTED = "#6E6C65"     # subtitles, ticks, notes
FAINT = "#75726A"     # small uppercase labels, secondary code text (4.8:1 on white)
GRID = "#E6E2DA"      # gridlines
AXIS = "#B9B6AE"      # axis lines (vertical bars), connectors
RULE = "#E2DFD7"      # card borders, rules

# ---- named colors. Color carries meaning across a write-up, so keep the roles fixed:
#   coral = the baseline / no intervention / the bad outcome
#   blue  = the intervention / the point you are making
#   sage  = a second kind of intervention (fine-tuning, a different prompt)
#   beige = untouched / reference
#   gray  = everything that is not the point (use with one accent)
#   dark  = a reference bar that should still read clearly (e.g. the untrained model)
# Accessibility (tests/test_access.py holds these): coral, blue, sage, dark, navy and clay reach 3:1 against the
# white background; the role colors stay at least 10 CIEDE2000 apart for protanopia, deuteranopia and tritanopia;
# gray and beige are deliberately light context, so values on them are always labeled.
PALETTE: dict[str, str] = {
    "coral": "#D47D5E",
    "blue": "#5E91C2",
    "sage": "#74897F",
    "beige": "#EADDC2",
    "gray": "#C2BFB9",
    "dark": "#67645C",
    "light-blue": "#A9C3DE",
    "deep-blue": "#3F73A8",
    "navy": "#2F5E8C",
    "light-sage": "#A8BBB1",
    "deep-sage": "#56705F",
    "light-coral": "#EDB9A4",
    "clay": "#A85F43",
    "ink": INK,
    "ink2": INK2,
    "muted": MUTED,
}

# Pale fills for tiles and backgrounds (text on them stays ink).
TINT: dict[str, str] = {
    "coral": "#F3D9CD",
    "beige": "#EFE8DD",
    "gray": "#ECE9E3",
    "blue": "#DDE5EE",
    "sage": "#DCE7DF",
    "surface": SURFACE,
}

# Default order when several series need colors and none were given: each next color is the one most distinct from
# those before it for color-blind readers. Series past the sixth are muted gray: mute what isn't the point.
SERIES = ["coral", "blue", "sage", "navy", "dark", "clay"]

# Darker fills for "strong" tiles, so white text on them reaches 4.5:1.
STRONG = {"blue": "deep-blue", "coral": "clay", "sage": "deep-sage"}

# Sequential scales (low end -> high end) for heatmaps.
SCALES: dict[str, tuple[str, str]] = {
    "blue": (SURFACE, "#3F73A8"),
    "coral": (SURFACE, "#C2603D"),
    "sage": (SURFACE, "#4E6A5B"),
    "green": ("#E3EDE3", "#4E9466"),
}

# ---- type
SERIF = "Newsreader, 'Iowan Old Style', Georgia, serif"
SANS = "'DM Sans', 'Helvetica Neue', Arial, sans-serif"
MONO = "'JetBrains Mono', Menlo, monospace"
FAMILIES = {"serif": SERIF, "sans": SANS, "mono": MONO}
GOOGLE_FONTS = ("https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700;"
                "1,9..40,400&family=JetBrains+Mono:wght@400;600&family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;"
                "0,6..72,600;1,6..72,400&display=swap")

# ---- frame geometry (CSS px; PNGs render at 2x)
WIDTH = 960           # content width; the figure is WIDTH + 2 * PAD_X wide (1008 px, 2016 px at 2x)
PAD_X = 24
PAD_TOP = 22
PAD_BOTTOM = 18

# claim frame: left-aligned serif claim title, muted sans subtitle
TITLE_SIZE = 22
SUBTITLE_SIZE = 13.5
HEADER_GAP = 14       # header -> legend/body
LEGEND_SIZE = 13
LEGEND_GAP = 12       # legend -> body

# blog frame: centered serif title and subtitle, legend below
BLOG_TITLE_SIZE = 16.5

TICK_SIZE = 12
MIN_TEXT = 12        # no text smaller than this, at 1x


# ---- sizes: where a figure goes
@dataclass(frozen=True)
class Size:
    """A destination. width: the whole figure in layout px; plot: the body height that bar, line, scatter and
    distribution charts share, so figures of one size line up; title: the claim title size; height: pad to this
    total height (slides); inches: the printed width, None on screens; scale: PNG pixels per layout px on screens
    (print sizes render at 300 dpi). Text keeps its px sizes, so a narrower layout prints larger."""
    width: float
    plot: float
    title: float
    height: float | None = None
    inches: float | None = None
    scale: float = 2


SIZES: dict[str, Size] = {
    "screen": Size(width=1008, plot=300, title=22),                          # posts, Discord, artifacts: 2016 px
    "slide": Size(width=640, plot=230, title=22, height=360, scale=3),       # a full 16:9 slide: 1920 x 1080 px
    "paper": Size(width=748, plot=270, title=16, inches=6.75),               # two-column paper, full text width
    "column": Size(width=360, plot=210, title=15, inches=3.25),              # one column of it; text prints at 8 pt
}
DPI = 300

_size: contextvars.ContextVar[Size | None] = contextvars.ContextVar("vellum_size", default=None)


def size_of(s: str | Size | None) -> Size:
    if isinstance(s, Size):
        return s
    if s is None:
        return SIZES["screen"]
    if s not in SIZES:
        raise ValueError(f"unknown size {s!r}; use one of: {', '.join(SIZES)}, or a vl.Size(...)")
    return SIZES[s]


def current_size() -> Size:
    """The size of the figure being drawn (screen outside a figure)."""
    return _size.get() or SIZES["screen"]


def color(c: str | None, default: str = "blue") -> str:
    """Resolve a palette name ('coral', 'light-blue', ...) or pass a hex color through."""
    if c is None:
        c = default
    if c.startswith(("#", "rgb")) or c in ("none", "transparent", "white"):
        return c
    key = c.lower().replace("_", "-").replace(" ", "-")
    if key in PALETTE:
        return PALETTE[key]
    raise ValueError(f"unknown color {c!r}; use a hex value or one of: {', '.join(PALETTE)}")


def tint(c: str) -> str:
    """Pale version of a palette color for backgrounds (falls back to mixing with the background)."""
    key = c.lower()
    if key in TINT:
        return TINT[key]
    return mix(color(c), BG, 0.72)


def mix(a: str, b: str, t: float) -> str:
    """Linear sRGB mix: t=0 gives a, t=1 gives b."""
    pa, pb = _rgb(a), _rgb(b)
    return "#" + "".join(f"{round(pa[i] + (pb[i] - pa[i]) * t):02X}" for i in range(3))


def _rgb(h: str) -> tuple[int, int, int]:
    h = color(h).lstrip("#")
    if len(h) == 3:
        h = "".join(ch * 2 for ch in h)
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def luminance(c: str) -> float:
    """WCAG relative luminance, used to pick white or ink text on a fill."""
    def ch(v: int) -> float:
        s = v / 255
        return s / 12.92 if s <= 0.03928 else ((s + 0.055) / 1.055) ** 2.4
    r, g, b = _rgb(c)
    return 0.2126 * ch(r) + 0.7152 * ch(g) + 0.0722 * ch(b)


def text_on(fill: str, soft: bool = False) -> str:
    """Text color for a fill: white or ink, whichever contrasts more, and black when neither reaches 4.5:1.
    soft=True gives the quieter color for secondary lines when it still reaches 4.5:1."""
    from .access import contrast
    main = max(("#FFFFFF", INK), key=lambda t: contrast(t, fill))
    if contrast(main, fill) < 4.5:
        main = max(("#FFFFFF", "#000000"), key=lambda t: contrast(t, fill))
    if soft:
        quiet = mix(main, fill, 0.15) if main == "#FFFFFF" else INK2
        if contrast(quiet, fill) >= 4.5:
            return quiet
    return main


def readable(c: str, bg: str = BG, ratio: float = 4.5) -> str:
    """The color itself if text in it reaches `ratio` against bg, else the lightest darker shade that does."""
    from .access import contrast
    c = color(c)
    for k in range(21):
        out = mix(c, INK, k / 20)
        if contrast(out, bg) >= ratio:
            return out
    return INK


def strong_fill(c: str) -> str:
    """A fill dark enough for white text: the palette's deep variant, else the color darkened until it is."""
    key = c.lower().replace("_", "-").replace(" ", "-")
    out = color(STRONG.get(key, c))
    return out if text_on(out) == "#FFFFFF" else readable(out, "#FFFFFF")
