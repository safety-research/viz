"""Grouped bars.

Each model's rate without and with the intervention.
"""
import viz

# Share of 200 harmful requests each model complied with: no system prompt, safety system prompt.
complied = {
    "Model A": [12.5, 4.0], "Model B": [18.0, 5.5], "Model C": [22.5, 6.0], "Model D": [27.0, 8.5],
    "Model E": [31.5, 7.0], "Model F": [35.0, 9.5], "Model G": [41.5, 11.0], "Model H": [46.0, 10.5],
    "Model I": [52.5, 14.0], "Model J": [58.0, 12.5],
}
fig = viz.bars(
    complied, series=["No system prompt", "Safety system prompt"], ylabel="Harmful requests complied with",
    roles={"baseline": "No system prompt", "intervention": "Safety system prompt"},
    title="The safety system prompt cut harmful compliance for all ten models")
fig.save("02_bars.png")
