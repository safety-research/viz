"""An effect and its interval for each model, against zero."""
import viz

# The change in wrong answers with search (percentage points) and its 95% interval, per model.
change = {"Model A": -8.5, "Model B": -12.5, "Model C": -16.5, "Model D": -18.5, "Model E": -24.5,
          "Model F": -25.5, "Model G": -30.5, "Model H": -35.5, "Model I": -38.5, "Model J": -45.5}
ci = {"Model A": (-13.8, -3.2), "Model B": (-18.7, -6.3), "Model C": (-23.2, -9.8), "Model D": (-25.8, -11.2),
      "Model E": (-31.8, -17.2), "Model F": (-33.3, -17.7), "Model G": (-38.6, -22.4), "Model H": (-43.6, -27.4),
      "Model I": (-46.9, -30.1), "Model J": (-53.7, -37.3)}
fig = viz.dotplot(
    change, ci=ci, ref=0, unit="", decimals=0, xlabel="Change in wrong answers with search (percentage points)",
    title="Search cut each model's wrong answers by 8 to 46 points")
fig.save("04_dotplot.png")
