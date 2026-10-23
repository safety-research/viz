"""Ratings before and after.

Each model's judge rating before and after training, joined by a line.
"""
import viz

# Mean honesty rating from an LLM judge, 1 (not at all) to 7 (fully), before and after training. None: not rated.
ratings = {
    "Model A": (5.1, 6.2), "Model B": (4.6, 6.0), "Model C": (None, None), "Model D": (4.2, 5.9),
    "Model E": (3.9, 5.7), "Model F": (None, None), "Model G": (3.4, 5.5), "Model H": (3.0, 5.6),
    "Model I": (2.7, 5.2), "Model J": (2.5, 5.0),
}
fig = viz.dumbbell(
    ratings, series=("Before training", "After training"), unit="", ticks=[1, 2, 3, 4, 5, 6, 7],
    roles={"baseline": "Before training", "intervention": "After training"},
    missing="not rated", title="Every rated model got a higher honesty rating after training")
fig.save("25_dumbbell.png")
