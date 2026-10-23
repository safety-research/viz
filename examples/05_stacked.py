"""Outcome breakdown.

The share of each outcome per condition; orange is the bad outcome.
"""
import viz

# What the model did on 400 coding tasks with a failing test.
fig = viz.stacked(
    {"Plain RL": [41, 18, 41], "Inoculation prompt": [76, 12, 12]},
    series=["Fixed the bug", "Gave up", "Special-cased the test"], colors=["blue", "beige", "coral"],
    title="With the inoculation prompt, special-cased tests fell from 41% to 12%")
fig.save("05_stacked.png")
