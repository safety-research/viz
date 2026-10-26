"""Confusion matrix.

What a monitor flagged against what really happened.
"""
import viz

# 200 RL episodes: whether the model hacked the reward, and whether the monitor flagged the episode.
episodes = {"Hacked": {"Flagged": 41, "Not flagged": 12}, "Did not hack": {"Flagged": 7, "Not flagged": 140}}
fig = viz.heatmap(episodes, unit="", label="Episodes",
                  title="The monitor caught 41 of 53 hacks with 7 false alarms")
fig.save("19_heatmap_confusion.png")
