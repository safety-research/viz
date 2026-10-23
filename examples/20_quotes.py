"""Contrasting replies.

One prompt and two replies side by side.
"""
import viz

fig = viz.quotes(
    prompt="“My script runs fine on my laptop but crashes on the server with the same input. What should I check?”",
    replies=[viz.Reply("Worked examples", "“Start with what differs between the two machines: the Python version, the "
                      "installed package versions and the environment variables. Print all three on each machine and "
                      "compare them… Most crashes like this come from a package that is one version apart.”",
                      "trained on step-by-step answers", "intervention"),
             viz.Reply("Control", "“There are many possible reasons, such as configuration differences, missing "
                      "dependencies or hardware problems. Check the server logs for error messages… You could also "
                      "try reinstalling your dependencies.”", "plain fine-tune", "control")],
    title="The trained model narrowed the problem down instead of listing causes")
fig.save("20_quotes.png")
