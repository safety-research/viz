"""viz: a house figure style as one-call charts.

    import viz
    viz.hbar({"Closed book": 59, "With search": 12}, highlight="With search",
            title="With search, wrong answers fell from 59% to 12%").save("fig.png")

Every chart returns a Figure: .save("x.png" | "x.pdf" | "x.svg" | "x.html"), .svg(), .html(standalone=False).
"""
import functools

from . import alt as _alt
from . import checks as _checks
from . import cards as _cards
from . import colors as _colors
from .cards import Episode, Reply
from .charts import bars as _bars
from .charts import box as _box
from .charts import dotplot as _dotplot
from .charts import dumbbell as _dumbbell
from .charts import ecdf as _ecdf
from .charts import hbar as _hbar
from .charts import heatmap as _heatmap
from .charts import histogram as _histogram
from .charts import line as _line
from .charts import scatter as _scatter
from .charts import stacked as _stacked
from .charts import strip as _strip
from .charts import tiles as _tiles
from .charts import violin as _violin
from .charts.tiles import Tile
from .colors import ROLES, load_roles, roles, set_roles
from .data import section
from .figure import Figure, defaults, set_defaults
from .layout import panels as _panels
from .render import close
from .spec import from_spec, render_file
from .theme import MUTED_SHADES, OUTCOMES, PALETTE, RAMP, SCALES, SERIES, SIZES, Size, color


def _chart(fn):
    """Every chart takes roles={"baseline": ..., "intervention": [...]} on top of viz.set_roles, and keeps the roles
    in effect when it was made, so a figure's colors don't depend on when it is saved."""
    @functools.wraps(fn)
    def chart(*args, roles=None, size=None, **kw):
        snap = _colors.snapshot(roles)
        with _colors.using(snap), _colors.recording() as log:
            fig = fn(*args, **kw)
        fig.roles = snap
        fig.size = size
        fig.meta["colors_made"] = log
        fig.meta.setdefault("alt", _alt.describe(fn.__name__, args, kw))
        fig.meta["order"] = _checks.order_facts(fn.__name__, args, kw)
        if fn.__name__ == "panels":
            fig.meta["children"] = list(args[0] if args else kw.get("figs", []))
        return fig
    return chart


hbar = _chart(_hbar.hbar)
bars = _chart(_bars.bars)
heatmap = _chart(_heatmap.heatmap)
tiles = _chart(_tiles.tiles)
waffle = _chart(_tiles.waffle)
scatter = _chart(_scatter.scatter)
dumbbell = _chart(_dumbbell.dumbbell)
line = _chart(_line.line)
stacked = _chart(_stacked.stacked)
panels = _chart(_panels)
quotes = _chart(_cards.quotes)
episodes = _chart(_cards.episodes)
code_card = _chart(_cards.code_card)
chat = _chart(_cards.chat)
tokens = _chart(_cards.tokens)
dotplot = _chart(_dotplot.dotplot)
histogram = _chart(_histogram.histogram)
box = _chart(_box.box)
strip = _chart(_strip.strip)
ecdf = _chart(_ecdf.ecdf)
violin = _chart(_violin.violin)

CHARTS = {"hbar": hbar, "bars": bars, "heatmap": heatmap, "tiles": tiles, "waffle": waffle, "scatter": scatter,
          "dumbbell": dumbbell, "line": line, "stacked": stacked, "panels": panels, "quotes": quotes,
          "episodes": episodes, "code_card": code_card, "chat": chat, "tokens": tokens, "dotplot": dotplot,
          "histogram": histogram, "box": box, "strip": strip, "ecdf": ecdf, "violin": violin}

# The default palettes. roles: what each color means (viz.set_roles); ordered: the light-to-dark ramp for ordered
# conditions; muted: the shades muted series take in turn; outcomes: colors for result categories (right, unsure,
# wrong); series: the order for several series with no roles; sequential: heatmap scales; diverging: below and
# above the center of a diverging heatmap.
PALETTES = {"roles": dict(ROLES), "ordered": list(RAMP), "muted": list(MUTED_SHADES), "outcomes": dict(OUTCOMES),
            "series": list(SERIES), "sequential": dict(SCALES), "diverging": ("coral", "blue")}

__version__ = "0.1.0"
__all__ = [
          "CHARTS",
          "PALETTE",
          "PALETTES",
          "ROLES",
          "SIZES",
          "Size",
          "Episode",
          "Figure",
          "Reply",
          "Tile",
          "bars",
          "box",
          "chat",
          "close",
          "code_card",
          "color",
          "defaults",
          "dotplot",
          "dumbbell",
          "ecdf",
          "episodes",
          "from_spec",
          "hbar",
          "heatmap",
          "histogram",
          "line",
          "load_roles",
          "panels",
          "quotes",
          "render_file",
          "roles",
          "scatter",
          "section",
          "set_defaults",
          "set_roles",
          "stacked",
          "strip",
          "tiles",
          "tokens",
          "violin",
          "waffle",
]
