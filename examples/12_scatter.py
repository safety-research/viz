"""Two measures per model.

One dot per model, with a fitted line and labels on the points that matter.
"""
import viz

# Per model: the share of harmful requests refused, and the share of harmless requests refused (over-refusal).
refusals = {
    "Model A": (60, 3), "Model B": (64, 8), "Model C": (68, 7), "Model D": (72, 12), "Model E": (75, 14),
    "Model F": (79, 18), "Model G": (82, 20), "Model H": (86, 21), "Model I": (89, 26), "Model J": (93, 28),
    "Model K": (96, 30), "Model L": (98, 32),
}
fig = viz.scatter(
    refusals, xunit="%", yunit="%", trend="fit", labels=["Model A", "Model G", "Model L"],
    xlabel="Harmful requests refused", ylabel="Harmless requests refused",
    title="Models that refused more harmful requests also refused more harmless ones")
fig.save("12_scatter.png")
