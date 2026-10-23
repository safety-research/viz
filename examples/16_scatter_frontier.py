"""Score against cost.

One dot per model, with the Pareto frontier through the best trade-offs.
"""
import viz

# Per model: dollars per million tokens, and accuracy (%).
models = {"Model A": (15.0, 88), "Model B": (10.0, 84), "Model C": (8.0, 86), "Model D": (4.0, 81),
          "Model E": (3.0, 76), "Model F": (2.5, 79), "Model G": (1.2, 70), "Model H": (0.8, 72),
          "Model I": (0.6, 57), "Model J": (0.3, 58)}
fig = viz.scatter(
    models, frontier="upper-left", labels=True, yunit="%", yticks=[50, 60, 70, 80, 90],
    xlabel="Cost per million tokens ($)", ylabel="Accuracy",
    title="Six of ten models were on the cost-accuracy frontier")
fig.save("16_scatter_frontier.png")
