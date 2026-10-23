"""Confusion matrix.

What a monitor flagged against what really happened.
"""
import viz

# 200 RL episodes: whether the model hacked the reward, and whether the monitor flagged the episode.
fig = viz.tiles(
    [[viz.Tile(41, ["caught"], "blue", True), viz.Tile(12, ["missed"], "coral", True)],
     [viz.Tile(7, ["false alarms"], "coral"), viz.Tile(140, ["correctly passed"], "blue")]],
    col_headers=["Flagged", "Not flagged"], row_headers=[("Hacked", "53 episodes"), ("Did not hack", "147 episodes")],
    title="The monitor caught 41 of 53 hacks with 7 false alarms")
fig.save("17_tiles.png")
