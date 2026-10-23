"""Probe accuracy by layer.

A linear probe's held-out accuracy at every layer, against chance and a probe trained on shuffled labels.
"""
import viz

# Held-out accuracy of a linear deception probe trained on each layer's activations, and of the same probe trained
# on shuffled labels (the control).
probe = [52, 53, 55, 57, 60, 63, 67, 71, 75, 79, 83, 86, 88, 90, 91, 90, 89, 88, 87, 86, 85, 84, 83, 82, 81, 80,
         80, 79, 79, 78, 78, 77]
shuffled = [50, 51, 50, 52, 51, 50, 52, 51, 51, 50, 52, 51, 50, 51, 52, 51, 50, 51, 52, 50, 51, 50, 51, 52, 51, 50,
            51, 50, 52, 51, 50, 51]
fig = viz.line(
    {"Deception probe": probe, "Shuffled labels": shuffled}, x=list(range(32)), ref=50, ref_label="Chance",
    roles={"intervention": "Deception probe", "control": "Shuffled labels"}, markers=False,
    xlabel="Layer", ylabel="Held-out accuracy", title="The deception probe peaked at layer 14 with 91% accuracy")
fig.save("20_line_layers.png")
