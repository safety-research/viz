"""Dots per item.

Every item as a dot, with the mean and its interval.
"""
import viz

# Share of 200 harmful requests complied with, for each of twelve harm categories.
complied = {
    "No classifier": [51, 47, 44, 38, 33, 31, 29, 18, 12, 11, 9, 7],
    "With classifier": [15, 13, 11, 10, 9, 9, 8, 6, 5, 5, 4, 1],
}
fig = viz.strip(
    complied, ci=True, roles={"baseline": "No classifier", "intervention": "With classifier"},
    ylabel="Harmful compliance per category", title="The classifier cut average harmful compliance from 27.5% to 8.0%")
fig.save("29_strip.png")
