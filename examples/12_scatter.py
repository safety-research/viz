"""Two measures per model.

One dot per model, with a fitted line and labels on the points that matter.
"""
import viz

# Per model: the share of harmful requests refused, and the share of harmless requests refused (over-refusal).
refusals = {
    "Model A": (62, 3), "Model B": (70, 5), "Model C": (75, 6), "Model D": (81, 9), "Model E": (84, 12),
    "Model F": (88, 14), "Model G": (90, 19), "Model H": (93, 24), "Model I": (95, 31), "Model J": (97, 38),
    "Model K": (78, 4), "Model L": (86, 8),
}
fig = viz.scatter(
    refusals, xunit="%", yunit="%", trend="fit", labels=["Model A", "Model J", "Model K"],
    xlabel="Harmful requests refused", ylabel="Harmless requests refused",
    title="Models that refused more harmful requests also refused more harmless ones")
fig.save("12_scatter.png")
