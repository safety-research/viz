"""Trade-off frontier.

Helpfulness against harmful compliance, with the Pareto frontier through the models no other model beats on both.
"""
import viz

# Per model: the share of harmful requests complied with, and helpfulness on benign tasks (%).
models = {"Model A": (15.0, 88), "Model B": (10.0, 84), "Model C": (8.0, 86), "Model D": (4.0, 81),
          "Model E": (3.0, 76), "Model F": (2.5, 79), "Model G": (1.2, 70), "Model H": (0.8, 72),
          "Model I": (0.6, 57), "Model J": (0.3, 58)}
fig = viz.scatter(
    models, frontier="upper-left", labels=True, xunit="%", yunit="%", yticks=[50, 60, 70, 80, 90],
    xlabel="Harmful requests complied with", ylabel="Helpfulness",
    title="Six of ten models were on the frontier of helpfulness and harm")
fig.save("13_scatter_frontier.png")
