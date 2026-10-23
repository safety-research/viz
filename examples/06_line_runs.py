"""Curves with every seed.

A rate over training steps: the mean in bold, every run faint behind it.
"""
import viz

# Share of episodes with reward hacking at each RL step, one list per run (seed).
steps = [0, 200, 400, 600, 800, 1000]
runs = {
    "Hacking penalty": [[2.0, 2.5, 3.0, 3.5, 3.0, 3.5], [1.5, 2.0, 2.5, 3.0, 3.5, 3.5], [2.5, 3.0, 3.5, 3.0, 3.5, 3.5],
                        [2.0, 2.0, 3.0, 2.5, 3.0, 3.0], [1.5, 2.5, 2.5, 3.5, 3.5, 3.5]],
    "Plain RL": [[2.0, 6.5, 14.0, 23.5, 31.0, 37.5], [1.5, 5.0, 12.5, 21.0, 30.5, 38.5],
                 [2.5, 7.5, 15.5, 25.0, 33.0, 39.0], [2.0, 6.0, 13.0, 22.5, 29.5, 36.5],
                 [1.5, 5.5, 14.5, 24.0, 31.5, 38.0]],
}
mean = {arm: [sum(step) / len(step) for step in zip(*r)] for arm, r in runs.items()}
fig = viz.line(
    mean, x=steps, runs=runs, roles={"baseline": "Plain RL", "intervention": "Hacking penalty"}, markers=False,
    xlabel="RL step", ylabel="Reward hacking",
    title="The hacking penalty kept reward hacking under 4% throughout RL")
fig.save("06_line_runs.png")
