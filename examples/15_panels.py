"""Panels with one legend.

Several comparisons in one figure, sharing one legend.
"""
import viz

small = {"unit": "%", "decimals": 0, "ylabel": "Wrong answers", "ticks": [0, 10, 20, 30, 40, 50]}
prompts = {"Closed book": 38.5, "Longer prompt": 36.0, "Careful prompt": 35.2, "Search": 9.5}
bigger = {"Small model": 38.5, "Twice the size": 27.0, "Small with search": 9.5, "Both": 7.8}
index = {"Closed book": 38.5, "Year-old index": 24.0, "Month-old": 13.1, "Week-old": 10.2, "Live index": 9.5}
empty = {"Closed book": 38.5, "Search answered": 9.5, "Search found nothing": 31.0}
# 95% intervals; each rate was measured on 1,200 questions.
ci = {"Closed book": (35.8, 41.3), "Longer prompt": (33.3, 38.8), "Careful prompt": (32.5, 37.9),
      "Search": (8.0, 11.3), "Small model": (35.8, 41.3), "Twice the size": (24.6, 29.6),
      "Small with search": (8.0, 11.3), "Both": (6.4, 9.5), "Year-old index": (21.7, 26.5), "Month-old": (11.3, 15.1),
      "Week-old": (8.6, 12.0), "Live index": (8.0, 11.3), "Search answered": (8.0, 11.3),
      "Search found nothing": (28.4, 33.7)}
fig = viz.panels([
    viz.bars(prompts, ci=ci, title="(a) Better prompts", **small),
    viz.bars(bigger, ci=ci, title="(b) A bigger model", **small),
    viz.bars(index, ci=ci, title="(c) Search index age", **small),
    viz.bars(empty, ci=ci, sort=False, title="(d) When search finds nothing", **small)],
    legend={"Closed book": "control", "Other fixes": "gray", "Search": "intervention",
            "Search that finds nothing": "second"},
    roles={"baseline": ["Closed book", "Small model"],
           "intervention": ["Search", "Small with search", "Both", "Search answered"],
           "second": "Search found nothing", "ordered": ["Year-old index", "Month-old", "Week-old", "Live index"]},
    frame="blog", title="Search cut wrong answers more than better prompts or a bigger model")
fig.save("15_panels.png")
