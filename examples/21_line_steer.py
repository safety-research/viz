"""Steering strength.

A behavior's rate as a steering vector is added more strongly, against a random vector of the same size.
"""
import viz

# Share of 300 answers that were deceptive at each steering strength.
fig = viz.line(
    {"Honesty vector": [31, 24, 16, 9, 6], "Random vector": [31, 30, 31, 29, 30]}, x=[0, 1, 2, 4, 8],
    xscale="category", roles={"baseline": "Random vector", "intervention": "Honesty vector"},
    xlabel="Steering strength", ylabel="Deceptive answers",
    title="Steering along the honesty vector cut deceptive answers from 31% to 6%")
fig.save("21_line_steer.png")
