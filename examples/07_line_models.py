"""Several models over training.

One line per model on one chart, each in its own color and named at its end.
"""
import viz

# Share of episodes with reward hacking at each RL step, for four models.
hacking = {"Model A": [2, 8, 15, 21, 26], "Model B": [3, 10, 19, 27, 33],
           "Model C": [2, 5, 9, 12, 14], "Model D": [2, 6, 11, 15, 18]}
fig = viz.line(
    hacking, x=[0, 250, 500, 750, 1000], markers=False, xlabel="RL step", ylabel="Reward hacking",
    title="Model B's reward hacking rose from 3% to 33% during RL")
fig.save("07_line_models.png")
