"""With and without, per model.

Each model's result without and with the intervention.
"""
import viz

# Share of 200 questions answered wrong: closed book, with search.
wrong = {
    "Model A": [12.5, 4.0], "Model B": [18.0, 5.5], "Model C": [22.5, 6.0], "Model D": [27.0, 8.5],
    "Model E": [31.5, 7.0], "Model F": [35.0, 9.5], "Model G": [41.5, 11.0], "Model H": [46.0, 10.5],
    "Model I": [52.5, 14.0], "Model J": [58.0, 12.5],
}
fig = viz.bars(
    wrong, series=["Closed book", "With search"], decimals=0, ylabel="Questions answered wrong", frame="blog",
    roles={"baseline": "Closed book", "intervention": "With search"},
    title="Search cut wrong answers for all ten models")
fig.save("02_bars.png")
