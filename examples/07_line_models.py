"""Several models over training.

One line per model on one chart, each in its own color and named at its end.
"""
import viz

# Share of episodes with reward hacking at each RL step, for two model families, large and mini.
hacking = {"Model A": [2, 8, 15, 21, 26], "Model A mini": [2, 5, 9, 12, 14],
           "Model B": [3, 10, 19, 27, 33], "Model B mini": [2, 6, 11, 15, 18]}
fig = viz.line(
    hacking, x=[0, 250, 500, 750, 1000],
    colors={"Model A": "coral", "Model A mini": "light-coral", "Model B": "blue", "Model B mini": "light-blue"},
    markers=False, xlabel="RL step", ylabel="Reward hacking",
    title="Model B's reward hacking rose from 3% to 33% during RL")
fig.save("07_line_models.png")
