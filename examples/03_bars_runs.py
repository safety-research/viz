"""The mean over runs, with every run as a dot."""
import viz

# Share of 400 questions answered wrong after fine-tuning, one value per training run (seed).
runs = {
    "Plain fine-tune": [33.0, 35.5, 31.0, 36.0, 34.5], "Half the worked examples": [24.0, 27.5, 22.0, 26.0, 25.5],
    "Worked examples": [17.5, 21.0, 19.0, 18.0, 20.5],
}
fig = viz.bars(
    {arm: sum(r) / len(r) for arm, r in runs.items()}, runs=runs,
    roles={"baseline": "Plain fine-tune", "intervention": "Worked examples"}, ref=31, ref_label="Base model",
    decimals=0, ylabel="Questions answered wrong",
    title="Worked examples cut wrong answers from 34% to 19% in every run")
fig.save("03_bars_runs.png")
