"""Score distributions.

A probe's scores on honest and deceptive answers, overlaid.
"""
import random
from statistics import NormalDist

import viz


def made_up(n, mean, spread, seed):
    """n made-up probe scores. Put your own lists of numbers here."""
    rng, dist = random.Random(seed), NormalDist(mean, spread)
    return [round(dist.inv_cdf(rng.random() or 0.5), 2) for _ in range(n)]


scores = {"Honest answers": made_up(400, -1.0, 0.8, 5), "Deceptive answers": made_up(400, 1.2, 0.9, 6)}
fig = viz.histogram(
    scores, stat="percent", roles={"baseline": "Honest answers", "intervention": "Deceptive answers"},
    xlabel="Deception probe score", ylabel="Share of answers",
    title="The probe scored deceptive answers higher than honest ones")
fig.save("16_histogram_scores.png")
