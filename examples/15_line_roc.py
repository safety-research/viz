"""ROC curves.

How many cases a monitor catches at each false-positive rate, against chance.
"""
import viz

# Hacks caught (true-positive rate) at each false-positive rate, from 1,000 labeled episodes per monitor.
roc = {"Chain-of-thought monitor": [(0, 0), (1, 52), (2, 66), (5, 80), (10, 88), (20, 94), (40, 98), (100, 100)],
       "Action-only monitor": [(0, 0), (1, 18), (2, 27), (5, 41), (10, 55), (20, 70), (40, 86), (100, 100)]}
fig = viz.line(
    roc, diagonal="Chance", marks={5: "5% false positives"}, xticks=[0, 20, 40, 60, 80, 100], xunit="%",
    roles={"baseline": "Action-only monitor", "intervention": "Chain-of-thought monitor"}, markers=False,
    end_labels=False, legend=True, xlabel="False-positive rate", ylabel="Hacks caught",
    title="At a 5% false-positive rate, the chain-of-thought monitor caught 80% of hacks")
fig.save("15_line_roc.png")
