"""Before and after for each model."""
import viz

# Mean helpfulness from 1 (not at all) to 7 (very): closed book, with search. None means not rated.
ratings = {
    "Model A": (5.1, 6.2), "Model B": (4.6, 6.0), "Model C": (None, None), "Model D": (4.2, 5.9),
    "Model E": (3.9, 5.7), "Model F": (None, None), "Model G": (3.4, 5.5), "Model H": (3.0, 5.6),
    "Model I": (2.7, 5.2), "Model J": (2.5, 5.0),
}
fig = viz.dumbbell(
    ratings, series=("Closed book", "With search"), unit="", decimals=1, ticks=[1, 2, 3, 4, 5, 6, 7],
    roles={"baseline": "Closed book", "intervention": "With search"},
    missing="not rated", title="Every rated model got higher helpfulness ratings with search")
fig.save("05_dumbbell.png")
