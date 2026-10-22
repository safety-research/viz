"""vellum: a house figure style as one-call charts.

    import vellum as vl
    vl.hbar({"Closed book": 59, "With search": 12}, highlight="With search",
            title="Search cut wrong answers fivefold", subtitle="Share of 400 questions answered wrong").save("fig.png")

Every chart returns a Figure: .save("x.png" | "x.pdf" | "x.svg" | "x.html"), .svg(), .html(standalone=False).
"""
from .cards import Episode, Reply, code_card, episodes, quotes
from .charts.bars import bars
from .charts.dumbbell import dumbbell
from .charts.hbar import hbar
from .charts.heatmap import heatmap
from .charts.line import line
from .charts.scatter import scatter
from .charts.stacked import stacked
from .charts.tiles import Tile, tiles, waffle
from .data import section
from .figure import Figure, defaults, set_defaults
from .layout import panels
from .render import close
from .spec import from_spec, render_file
from .theme import PALETTE, color

CHARTS = {"hbar": hbar, "bars": bars, "heatmap": heatmap, "tiles": tiles, "waffle": waffle, "scatter": scatter,
          "dumbbell": dumbbell, "line": line, "stacked": stacked, "panels": panels, "quotes": quotes,
          "episodes": episodes, "code_card": code_card}

__version__ = "0.1.0"
__all__ = [
          "CHARTS",
          "PALETTE",
          "Episode",
          "Figure",
          "Reply",
          "Tile",
          "bars",
          "close",
          "code_card",
          "color",
          "defaults",
          "dumbbell",
          "episodes",
          "from_spec",
          "hbar",
          "heatmap",
          "line",
          "panels",
          "quotes",
          "render_file",
          "scatter",
          "section",
          "set_defaults",
          "stacked",
          "tiles",
          "waffle",
]
