"""Where outcomes went.

The share of each outcome per condition; orange is the bad outcome.
"""
import viz

fig = viz.stacked(
    {"Closed book": [41, 0, 59], "With search": [76, 12, 12]}, series=["Right", "Said it didn’t know", "Wrong"],
    colors=["blue", "beige", "coral"],
    title="With search, wrong answers fell from 59% to 12%")
fig.save("12_stacked.png")
