"""Smoothed RL reward.

A noisy measure over training: the raw values faint, a moving average in bold.
"""
import math
import random
from statistics import NormalDist

import viz


def reward_curve(final, seed, n=201):
    """Made-up noisy RL reward that rises to `final`. Put your own lists of numbers here."""
    rng, noise = random.Random(seed), NormalDist(0, 0.09)
    return [round(0.2 + (final - 0.2) * (1 - math.exp(-4 * k / n)) + noise.inv_cdf(rng.random() or 0.5), 3)
            for k in range(n)]


steps = list(range(0, 2001, 10))
fig = viz.line(
    {"Without curriculum": reward_curve(0.48, 3), "With curriculum": reward_curve(0.74, 4)}, x=steps, smooth=0.9,
    roles={"baseline": "Without curriculum", "intervention": "With curriculum"}, unit="",
    xlabel="RL step", ylabel="Mean reward", title="The curriculum raised final mean reward from 0.472 to 0.720")
fig.save("08_line_smooth.png")
