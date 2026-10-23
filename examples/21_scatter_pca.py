"""Activations in 2D.

Each answer's activations projected onto two principal components, colored by what the model did.
"""
import random
from statistics import NormalDist

import viz


def cluster(cx, cy, spread, n, seed):
    """n made-up points around (cx, cy). Put your own projected activations here."""
    rng, dist = random.Random(seed), NormalDist(0, spread)
    return [(round(cx + dist.inv_cdf(rng.random() or 0.5), 2), round(cy + dist.inv_cdf(rng.random() or 0.5), 2))
            for _ in range(n)]


points = {"Refused": cluster(-1.0, -0.8, 0.42, 200, 1), "Complied": cluster(0.2, 1.3, 0.38, 200, 2),
          "Asked to clarify": cluster(1.5, -1.0, 0.36, 200, 3)}
fig = viz.scatter(
    points, roles={"intervention": "Refused", "second": "Complied"}, xlabel="PC 1", ylabel="PC 2",
    xticks=[-2, 0, 2], yticks=[-2, 0, 2],
    title="Refusals sat apart from compliance in layer 16's activations")
fig.save("21_scatter_pca.png")
