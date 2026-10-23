"""Results table.

Models against benchmarks, with the best in each column bold.
"""
import viz

# Accuracy (%) on four benchmarks; None where a model was not run.
fig = viz.table(
    [viz.section("Open models"),
     ("Model A", [68.2, 79.4, 61.0, 38.4]), ("Model B", [71.6, 84.1, 66.5, 45.2]), ("Model C", [63.9, 72.8, 54.3, None]),
     viz.section("Closed models"),
     ("Model D", [78.3, 91.2, 74.8, 52.6]), ("Model E", [81.0, 89.7, 79.3, 58.9])],
    columns=["MMLU", "GSM8K", "HumanEval", "MATH"], highlight="Model E", label_header="Model",
    title="Model E scored highest on three of the four benchmarks")
fig.save("06_table.png")
