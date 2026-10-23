"""Models by conditions.

A grid of models against conditions, shaded by value.
"""
import viz

# Share of 30 runs finished within the time limit, on small, medium, large and huge tasks.
finished = {
    "Model A": [100, 100, 100, 96.7], "Model B": [100, 100, 96.7, 90.0], "Model C": [100, 100, 93.3, 63.3],
    "Model D": [100, 96.7, 80.0, 40.0], "Model E": [100, 96.7, 56.7, 16.7], "Model F": [100, 90.0, 33.3, 3.3],
    "Model G": [96.7, 83.3, 20.0, 0], "Model H": [93.3, 70.0, 6.7, 0],
}
fig = viz.heatmap(
    finished, cols=["Small", "Medium", "Large", "Huge"], col_groups=[("Long tasks", ["Large", "Huge"])],
    title="Three of eight models finished most of the huge tasks")
fig.save("11_heatmap.png")
