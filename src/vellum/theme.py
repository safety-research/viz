"""The house style's tokens.

The values come from two looks: vertical coral and blue bars in the style of the Anthropic blog, and a clear
style with one claim per figure as a serif title, one accent on the point and direct labels.
"""
from __future__ import annotations

# ---- surfaces and ink
BG = "#FFFFFF"        # figure background: white
CARD = "#F1EEE8"      # quote cards
CARD_LIGHT = "#FFFDF9"  # code / tool cards
SURFACE = "#ECE8E1"   # empty heatmap cell, low end of sequential scales
INK = "#191918"       # titles, emphasized numbers
INK2 = "#3D3C38"      # labels, body text
MUTED = "#6E6C65"     # subtitles, ticks, notes
FAINT = "#8C887F"     # small uppercase labels, secondary code text
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
PALETTE: dict[str, str] = {
    "coral": "#D78365",
    "blue": "#5E91C2",
    "sage": "#74897F",
    "beige": "#DED3C4",
    "gray": "#CBC5BB",
    "dark": "#8C887F",
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

# Default order when several series need colors and none were given.
SERIES = ["coral", "blue", "sage", "beige", "light-blue", "dark", "deep-sage", "light-coral"]

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

TICK_SIZE = 11.5


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


def text_on(fill: str) -> str:
    """White on dark fills, ink on light ones."""
    return "#FFFFFF" if luminance(fill) < 0.28 else INK
