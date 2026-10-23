"""Models on benchmarks.

Several models on a few benchmarks: one bar per model in each group, each model in its own color.
"""
import viz

# Accuracy (%) of two model families, large and mini, on three benchmarks.
scores = {"MMLU": [86, 78, 83, 75], "GPQA": [59, 45, 55, 40], "SWE-bench": [49, 32, 45, 28]}
fig = viz.bars(
    scores, series=["Model A", "Model A mini", "Model B", "Model B mini"],
    colors=["coral", "light-coral", "blue", "light-blue"], sort=False, frame="blog", ylabel="Accuracy",
    title="Model A scored highest on all three benchmarks")
fig.save("11_bars_benchmarks.png")
