"""Distributions per condition, for many items each."""
import math
import random
from statistics import NormalDist

import viz


def made_up(n, median, spread, seed, digits=0):
    """n made-up values with a long right tail. Put your own lists of numbers here."""
    rng, dist = random.Random(seed), NormalDist(math.log(median), spread)
    return [round(math.exp(dist.inv_cdf(rng.random() or 0.5)), digits) for _ in range(n)]


seconds = {"Closed book": made_up(200, 3, 0.4, 23, 1), "Search snippets": made_up(200, 6, 0.45, 24, 1),
           "Full documents": made_up(200, 9.5, 0.5, 48, 1)}  # seconds to answer each of 200 questions
fig = viz.box(
    seconds, roles={"baseline": "Closed book", "intervention": "Full documents"}, unit="", decimals=1,
    ylabel="Seconds to answer", title="Full documents raised the median answer time from 2.9 to 9.2 seconds")
fig.save("08_box.png")
