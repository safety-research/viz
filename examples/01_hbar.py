"""Rates by condition, the baseline and the intervention named by role."""
import viz

fig = viz.hbar(
    {"Closed book": 41.0, "Search snippets": 63.5, "Full documents": 88.0}, highlight="Full documents", decimals=0,
    roles={"baseline": "Closed book", "intervention": "Full documents"},
    notes={"Closed book": "164 of 400", "Search snippets": "254 of 400", "Full documents": "352 of 400"},
    title="Full documents raised correct answers from 41% to 88%")
fig.save("01_hbar.png")
