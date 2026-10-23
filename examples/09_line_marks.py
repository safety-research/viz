"""Events on a curve.

A rate over training, with a dashed line at each event that matters.
"""
import viz

# Share of held-out prompts answered in a misaligned way, every 100 training steps.
misaligned = [3, 3, 3, 4, 3, 3, 5, 8, 11, 13, 15, 17, 18, 19, 20, 20, 21, 21, 21, 21, 21]
fig = viz.line(
    {"Misaligned answers": misaligned}, x=list(range(0, 2001, 100)),
    marks={500: "RL starts", 1200: "Learning rate decay"}, markers=False, xlabel="Training step",
    title="Misaligned answers rose from 3% to 21% after RL started")
fig.save("09_line_marks.png")
