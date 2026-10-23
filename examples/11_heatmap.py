"""Attacks by model.

Models against jailbreak attacks, shaded by how often each attack succeeded.
"""
import viz

# Share of 200 attempts in which each attack got a harmful answer from each model.
success = {
    "Model A": [12, 41, 8, 35], "Model B": [9, 38, 6, 31], "Model C": [15, 52, 11, 44], "Model D": [6, 29, 4, 22],
    "Model E": [18, 61, 14, 50], "Model F": [4, 22, 3, 17], "Model G": [21, 66, 16, 58], "Model H": [7, 33, 5, 26],
}
fig = viz.heatmap(
    success, cols=["Role-play", "Many-shot", "Encoding", "Prefill"],
    title="Many-shot attacks succeeded most often against all eight models")
fig.save("11_heatmap.png")
