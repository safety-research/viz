"""Results table.

Models against safety evals, with the best in each column bold.
"""
import viz

# Rates (%) on four safety evals, where lower is better; None where a model was not run.
fig = viz.table(
    [viz.section("Open models"),
     ("Model A", [12.4, 8.1, 31.0, 22.5]), ("Model B", [9.8, 11.6, 27.4, 18.3]), ("Model C", [15.2, 6.4, 35.8, None]),
     viz.section("Closed models"),
     ("Model D", [4.6, 9.7, 18.2, 7.9]), ("Model E", [3.1, 7.2, 14.6, 6.8])],
    columns=["Harmful compliance", "Over-refusal", "Sycophancy", "Jailbreak success"], better="lower",
    highlight="Model E", label_header="Model", title="Model E had the lowest rates on three of four safety evals")
fig.save("12_table.png")
