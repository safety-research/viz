"""Models on benchmarks.

Several models on a few benchmarks: one bar per model in each group, each model in its own color.
"""
import viz

# Accuracy (%) of four models on three benchmarks.
scores = {"MMLU": [86, 83, 78, 75], "GPQA": [59, 55, 45, 40], "SWE-bench": [49, 45, 32, 28]}
fig = viz.bars(
    scores, series=["Model A", "Model B", "Model C", "Model D"], sort=False, frame="blog", ylabel="Accuracy",
    title="Model A scored highest on all three benchmarks")
fig.save("11_bars_benchmarks.png")
