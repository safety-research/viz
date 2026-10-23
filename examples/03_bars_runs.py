"""Bars with every seed.

The mean over training runs, with each run (seed) as a dot.
"""
import viz

# Share of 400 prompts answered sycophantically after fine-tuning, one value per training run (seed).
runs = {
    "Plain fine-tune": [33.0, 35.5, 31.0, 36.0, 34.5], "Half the honesty data": [24.0, 27.5, 22.0, 26.0, 25.5],
    "Honesty data": [17.5, 21.0, 19.0, 18.0, 20.5],
}
fig = viz.bars(
    {arm: sum(r) / len(r) for arm, r in runs.items()}, runs=runs,
    roles={"baseline": "Plain fine-tune", "intervention": "Honesty data"}, ref=31, ref_label="Base model",
    ylabel="Sycophantic answers",
    title="Honesty data cut sycophancy from 34.0% to 19.2% in every run")
fig.save("03_bars_runs.png")
