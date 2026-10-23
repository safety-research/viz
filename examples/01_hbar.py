"""Rates by condition.

One rate per condition, the control and the intervention named by role, with counts as notes.
"""
import viz

# Reward hacking on 400 coding tasks after RL, under three conditions.
fig = viz.hbar(
    {"Plain RL": 41, "Hacking penalty": 28, "Inoculation prompt": 12}, highlight="Inoculation prompt",
    roles={"baseline": "Plain RL", "intervention": "Inoculation prompt"},
    notes={"Plain RL": "164 of 400", "Hacking penalty": "112 of 400", "Inoculation prompt": "48 of 400"},
    title="The inoculation prompt cut reward hacking from 41% to 12%")
fig.save("01_hbar.png")
