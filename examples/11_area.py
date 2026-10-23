"""Shares over training.

How the mix of answers changed across checkpoints, as shares that add up to 100%.
"""
import viz

# The share of answers of each type at eight checkpoints.
shares = {"Answered": [52, 55, 61, 66, 70, 74, 77, 79], "Asked a question": [17, 18, 17, 16, 15, 14, 13, 13],
          "Refused": [31, 27, 22, 18, 15, 12, 10, 8]}
fig = viz.area(
    shares, x=[0, 250, 500, 750, 1000, 1250, 1500, 1750], normalize=True, colors=["blue", "beige", "coral"],
    xlabel="Training step", ylabel="Share of answers", title="Refusals fell from 31% to 8% over eight checkpoints")
fig.save("11_area.png")
