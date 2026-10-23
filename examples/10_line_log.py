"""Scaling on log axes.

Loss against compute on log-log axes, one line per model size.
"""
import viz

# Validation loss at each amount of training compute (PF-days), per model size.
loss = {"Small model": [(0.01, 4.42), (0.03, 3.98), (0.1, 3.66), (0.3, 3.45), (1, 3.33), (3, 3.27)],
        "Medium model": [(0.03, 4.25), (0.1, 3.72), (0.3, 3.31), (1, 3.02), (3, 2.85), (10, 2.76)],
        "Large model": [(0.1, 4.05), (0.3, 3.46), (1, 2.98), (3, 2.62), (10, 2.39), (30, 2.25), (100, 2.17)]}
fig = viz.line(
    loss, xscale="log", yscale="log", unit="", decimals=1, markers=False,
    roles={"ordered": ["Small model", "Medium model", "Large model"]},
    xlabel="Training compute (PF-days)", ylabel="Validation loss",
    title="Larger models reached lower loss once compute passed 1 PF-day")
fig.save("10_line_log.png")
