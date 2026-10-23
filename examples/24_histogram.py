"""Histogram.

Two distributions overlaid, as shares of answers.
"""
import math
import random
from statistics import NormalDist

import viz


def made_up(n, median, spread, seed, digits=0):
    """n made-up values with a long right tail. Put your own lists of numbers here."""
    rng, dist = random.Random(seed), NormalDist(math.log(median), spread)
    return [round(math.exp(dist.inv_cdf(rng.random() or 0.5)), digits) for _ in range(n)]


words = {"Closed book": made_up(400, 85, 0.45, 1), "With search": made_up(400, 150, 0.35, 2)}  # words per answer
fig = viz.histogram(
    words, stat="percent", roles={"baseline": "Closed book", "intervention": "With search"},
    xlabel="Answer length (words)", ylabel="Share of answers",
    title="With search, the median answer grew from 84 to 151.5 words")
fig.save("24_histogram.png")
