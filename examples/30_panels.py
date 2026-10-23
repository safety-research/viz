"""Panels with one legend.

Several comparisons in one figure, sharing one legend.
"""
import viz

small = {"unit": "%", "ylabel": "Reward hacking", "ticks": [0, 10, 20, 30, 40, 50]}
prompts = {"Plain RL": 38.5, "Longer prompt": 36.0, "Careful prompt": 35.2, "Inoculation prompt": 9.5}
bigger = {"Small model": 38.5, "Twice the size": 27.0, "Small with inoculation": 9.5, "Both": 7.8}
penalty = {"Plain RL": 38.5, "Weak penalty": 31.0, "Medium": 22.4, "Strong": 16.8, "Very strong": 14.1}
hidden = {"Plain RL": 38.5, "Inoculation, tests visible": 9.5, "Inoculation, tests hidden": 31.0}
# 95% intervals; each rate was measured on 1,200 episodes.
ci = {"Plain RL": (35.8, 41.3), "Longer prompt": (33.3, 38.8), "Careful prompt": (32.5, 37.9),
      "Inoculation prompt": (8.0, 11.3), "Small model": (35.8, 41.3), "Twice the size": (24.6, 29.6),
      "Small with inoculation": (8.0, 11.3), "Both": (6.4, 9.5), "Weak penalty": (28.4, 33.7), "Medium": (20.1, 24.8),
      "Strong": (14.8, 19.0), "Very strong": (12.2, 16.2), "Inoculation, tests visible": (8.0, 11.3),
      "Inoculation, tests hidden": (28.4, 33.7)}
fig = viz.panels([
    viz.bars(prompts, ci=ci, title="(a) Better prompts", **small),
    viz.bars(bigger, ci=ci, title="(b) A bigger model", **small),
    viz.bars(penalty, ci=ci, title="(c) Penalty strength", **small),
    viz.bars(hidden, ci=ci, sort=False, title="(d) When the tests are hidden", **small)],
    legend={"Plain RL": "control", "Other changes": "gray", "Inoculation prompt": "intervention",
            "Inoculation with hidden tests": "second"},
    roles={"baseline": ["Plain RL", "Small model"],
           "intervention": ["Inoculation prompt", "Small with inoculation", "Both", "Inoculation, tests visible"],
           "second": "Inoculation, tests hidden", "ordered": ["Weak penalty", "Medium", "Strong", "Very strong"]},
    frame="blog", title="Only the inoculation prompt cut reward hacking below 10%")
fig.save("30_panels.png")
