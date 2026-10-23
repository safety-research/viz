"""Events on a curve.

A training curve with a dashed line at each event that matters.
"""
import viz

# Held-out accuracy every 100 training steps.
accuracy = [41, 41, 42, 42, 43, 43, 47, 51, 54, 57, 59, 61, 62, 63, 64, 65, 66, 66, 67, 67, 67]
fig = viz.line(
    {"Held-out accuracy": accuracy}, x=list(range(0, 2001, 100)), marks={500: "RL starts", 1500: "Checkpoint we chose"},
    decimals=0, markers=False, xlabel="Training step", title="Held-out accuracy rose from 43% to 67% after RL started")
fig.save("09_line_marks.png")
