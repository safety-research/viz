"""A training curve, with every run faint behind the mean."""
import viz

# Wrong answers at each training step, one list per run.
steps = [0, 200, 400, 600, 800, 1000]
runs = {
    "Worked examples": [[31.0, 25.5, 21.0, 19.5, 18.0, 17.5], [30.5, 26.5, 23.0, 20.5, 19.5, 18.5],
                        [31.5, 24.0, 20.5, 18.0, 17.0, 17.0], [31.0, 27.0, 22.5, 21.0, 19.0, 18.5],
                        [30.5, 25.0, 21.5, 19.0, 18.5, 17.5]],
    "Plain fine-tune": [[31.0, 31.5, 32.5, 32.0, 33.0, 33.5], [30.5, 32.0, 31.5, 33.0, 32.5, 33.0],
                        [31.5, 30.5, 32.0, 32.5, 33.5, 32.5], [31.0, 31.0, 33.0, 32.0, 32.0, 34.0],
                        [30.5, 32.5, 32.0, 33.5, 33.0, 33.0]],
}
mean = {arm: [sum(step) / len(step) for step in zip(*r)] for arm, r in runs.items()}
fig = viz.line(
    mean, x=steps, runs=runs,
    roles={"baseline": "Plain fine-tune", "intervention": "Worked examples"}, markers=False, decimals=0,
    xlabel="Training step", title="Worked examples cut wrong answers from 31% to 18% during training")
fig.save("06_line_runs.png")
