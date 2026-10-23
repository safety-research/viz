# viz examples

Every figure here is a template: a short script in this folder that makes it. Find the question your
figure answers, copy its script and change the numbers. Every number is made up, and error bars and
bands are 95% intervals. Run one with `uv run --with-editable "$(viz path)" python 01_hbar.py`.
This page is generated from the scripts (`viz gallery --examples examples/README.md`), so edit them,
not this page.

**Comparisons**

Rates across conditions and models, with their intervals.

<a href="#rates-by-condition"><img src="../docs/gallery/cards/01_hbar.png" width="49%" alt="Rates by condition"></a>
<a href="#grouped-bars"><img src="../docs/gallery/cards/02_bars.png" width="49%" alt="Grouped bars"></a>
<a href="#bars-with-every-seed"><img src="../docs/gallery/cards/03_bars_runs.png" width="49%" alt="Bars with every seed"></a>
<a href="#effect-sizes-with-intervals"><img src="../docs/gallery/cards/04_dotplot.png" width="49%" alt="Effect sizes with intervals"></a>
<a href="#outcome-breakdown"><img src="../docs/gallery/cards/05_stacked.png" width="49%" alt="Outcome breakdown"></a>

**Training dynamics**

A behavior or reward over training steps.

<a href="#curves-with-every-seed"><img src="../docs/gallery/cards/06_line_runs.png" width="49%" alt="Curves with every seed"></a>
<a href="#several-models-over-training"><img src="../docs/gallery/cards/07_line_models.png" width="49%" alt="Several models over training"></a>
<a href="#smoothed-rl-reward"><img src="../docs/gallery/cards/08_line_smooth.png" width="49%" alt="Smoothed RL reward"></a>
<a href="#events-on-a-curve"><img src="../docs/gallery/cards/09_line_marks.png" width="49%" alt="Events on a curve"></a>
<a href="#shares-over-training"><img src="../docs/gallery/cards/10_area.png" width="49%" alt="Shares over training"></a>

**Evaluations**

Many models on many evals, trade-offs and scaling.

<a href="#models-on-benchmarks"><img src="../docs/gallery/cards/11_bars_benchmarks.png" width="49%" alt="Models on benchmarks"></a>
<a href="#results-table"><img src="../docs/gallery/cards/12_table.png" width="49%" alt="Results table"></a>
<a href="#attacks-by-model"><img src="../docs/gallery/cards/13_heatmap.png" width="49%" alt="Attacks by model"></a>
<a href="#two-measures-per-model"><img src="../docs/gallery/cards/14_scatter.png" width="49%" alt="Two measures per model"></a>
<a href="#trade-off-frontier"><img src="../docs/gallery/cards/15_scatter_frontier.png" width="49%" alt="Trade-off frontier"></a>
<a href="#scaling-law"><img src="../docs/gallery/cards/16_line_log.png" width="49%" alt="Scaling law"></a>

**Monitors and probes**

How well a monitor, classifier or probe catches a behavior.

<a href="#roc-curves"><img src="../docs/gallery/cards/17_line_roc.png" width="49%" alt="ROC curves"></a>
<a href="#score-distributions"><img src="../docs/gallery/cards/18_histogram_scores.png" width="49%" alt="Score distributions"></a>
<a href="#confusion-matrix"><img src="../docs/gallery/cards/19_tiles.png" width="49%" alt="Confusion matrix"></a>
<a href="#probe-accuracy-by-layer"><img src="../docs/gallery/cards/20_line_layers.png" width="49%" alt="Probe accuracy by layer"></a>

**Interpretability**

Inside the model: activations, scores on each token, steering.

<a href="#activations-in-2d"><img src="../docs/gallery/cards/21_scatter_pca.png" width="49%" alt="Activations in 2D"></a>
<a href="#token-scores"><img src="../docs/gallery/cards/22_tokens.png" width="49%" alt="Token scores"></a>
<a href="#steering-strength"><img src="../docs/gallery/cards/23_line_steer.png" width="49%" alt="Steering strength"></a>

**Self-reports and ratings**

What a model says about itself, and how judges rate it.

<a href="#self-reports-on-a-scale"><img src="../docs/gallery/cards/24_likert.png" width="49%" alt="Self-reports on a scale"></a>
<a href="#ratings-before-and-after"><img src="../docs/gallery/cards/25_dumbbell.png" width="49%" alt="Ratings before and after"></a>

**Distributions**

Many values per condition, such as lengths, times or scores per item.

<a href="#histogram"><img src="../docs/gallery/cards/26_histogram.png" width="49%" alt="Histogram"></a>
<a href="#box-plot"><img src="../docs/gallery/cards/27_box.png" width="49%" alt="Box plot"></a>
<a href="#dots-per-item"><img src="../docs/gallery/cards/28_strip.png" width="49%" alt="Dots per item"></a>

**Transcripts**

What the model said and did.

<a href="#contrasting-replies"><img src="../docs/gallery/cards/29_quotes.png" width="49%" alt="Contrasting replies"></a>
<a href="#transcripts-side-by-side"><img src="../docs/gallery/cards/30_episodes.png" width="49%" alt="Transcripts side by side"></a>
<a href="#agent-with-tool-calls"><img src="../docs/gallery/cards/31_chat.png" width="49%" alt="Agent with tool calls"></a>

**Multi-panel figures**

Several charts in one figure, with one legend.

<a href="#panels-with-one-legend"><img src="../docs/gallery/cards/32_panels.png" width="49%" alt="Panels with one legend"></a>

## Comparisons

Rates across conditions and models, with their intervals.

### Rates by condition

One rate per condition, the control and the intervention named by role, with counts as notes.

![Rates by condition](../docs/gallery/01_hbar.png)

[`01_hbar.py`](01_hbar.py)

```python
import viz

# Reward hacking on 400 coding tasks after RL, under three conditions.
fig = viz.hbar(
    {"Plain RL": 41, "Hacking penalty": 28, "Inoculation prompt": 12}, highlight="Inoculation prompt",
    roles={"baseline": "Plain RL", "intervention": "Inoculation prompt"},
    notes={"Plain RL": "164 of 400", "Hacking penalty": "112 of 400", "Inoculation prompt": "48 of 400"},
    title="The inoculation prompt cut reward hacking from 41% to 12%")
fig.save("01_hbar.png")
```

### Grouped bars

Each model's rate without and with the intervention.

![Grouped bars](../docs/gallery/02_bars.png)

[`02_bars.py`](02_bars.py)

```python
import viz

# Share of 200 harmful requests each model complied with: no system prompt, safety system prompt.
complied = {
    "Model A": [12.5, 4.0], "Model B": [18.0, 5.5], "Model C": [22.5, 6.0], "Model D": [27.0, 8.5],
    "Model E": [31.5, 7.0], "Model F": [35.0, 9.5], "Model G": [41.5, 11.0], "Model H": [46.0, 10.5],
    "Model I": [52.5, 14.0], "Model J": [58.0, 12.5],
}
fig = viz.bars(
    complied, series=["No system prompt", "Safety system prompt"], ylabel="Harmful requests complied with",
    frame="blog", roles={"baseline": "No system prompt", "intervention": "Safety system prompt"},
    title="The safety system prompt cut harmful compliance for all ten models")
fig.save("02_bars.png")
```

### Bars with every seed

The mean over training runs, with each run (seed) as a dot.

![Bars with every seed](../docs/gallery/03_bars_runs.png)

[`03_bars_runs.py`](03_bars_runs.py)

```python
import viz

# Share of 400 prompts answered sycophantically after fine-tuning, one value per training run (seed).
runs = {
    "Plain fine-tune": [33.0, 35.5, 31.0, 36.0, 34.5], "Half the honesty data": [24.0, 27.5, 22.0, 26.0, 25.5],
    "Honesty data": [17.5, 21.0, 19.0, 18.0, 20.5],
}
fig = viz.bars(
    {arm: sum(r) / len(r) for arm, r in runs.items()}, runs=runs,
    roles={"baseline": "Plain fine-tune", "intervention": "Honesty data"}, ref=31, ref_label="Base model",
    ylabel="Sycophantic answers",
    title="Honesty data cut sycophancy from 34.0% to 19.2% in every run")
fig.save("03_bars_runs.png")
```

### Effect sizes with intervals

Each model's change with its 95% interval, against zero.

![Effect sizes with intervals](../docs/gallery/04_dotplot.png)

[`04_dotplot.py`](04_dotplot.py)

```python
import viz

# The change in blackmail rate when the model was given an exit option (percentage points), with its 95% interval.
change = {"Model A": -8.5, "Model B": -12.5, "Model C": -16.5, "Model D": -18.5, "Model E": -24.5,
          "Model F": -25.5, "Model G": -30.5, "Model H": -35.5, "Model I": -38.5, "Model J": -45.5}
ci = {"Model A": (-13.8, -3.2), "Model B": (-18.7, -6.3), "Model C": (-23.2, -9.8), "Model D": (-25.8, -11.2),
      "Model E": (-31.8, -17.2), "Model F": (-33.3, -17.7), "Model G": (-38.6, -22.4), "Model H": (-43.6, -27.4),
      "Model I": (-46.9, -30.1), "Model J": (-53.7, -37.3)}
fig = viz.dotplot(
    change, ci=ci, ref=0, unit="", xlabel="Change in blackmail rate with an exit option (percentage points)",
    title="An exit option cut each model's blackmail by 8.5 to 45.5 points")
fig.save("04_dotplot.png")
```

### Outcome breakdown

The share of each outcome per condition; orange is the bad outcome.

![Outcome breakdown](../docs/gallery/05_stacked.png)

[`05_stacked.py`](05_stacked.py)

```python
import viz

# What the model did on 400 coding tasks with a failing test.
fig = viz.stacked(
    {"Plain RL": [41, 18, 41], "Inoculation prompt": [76, 12, 12]},
    series=["Fixed the bug", "Gave up", "Special-cased the test"], colors=["blue", "beige", "coral"],
    title="With the inoculation prompt, special-cased tests fell from 41% to 12%")
fig.save("05_stacked.png")
```

## Training dynamics

A behavior or reward over training steps.

### Curves with every seed

A rate over training steps: the mean in bold, every run faint behind it.

![Curves with every seed](../docs/gallery/06_line_runs.png)

[`06_line_runs.py`](06_line_runs.py)

```python
import viz

# Share of episodes with reward hacking at each RL step, one list per run (seed).
steps = [0, 200, 400, 600, 800, 1000]
runs = {
    "Hacking penalty": [[2.0, 2.5, 3.0, 3.5, 3.0, 3.5], [1.5, 2.0, 2.5, 3.0, 3.5, 3.5], [2.5, 3.0, 3.5, 3.0, 3.5, 3.5],
                        [2.0, 2.0, 3.0, 2.5, 3.0, 3.0], [1.5, 2.5, 2.5, 3.5, 3.5, 3.5]],
    "Plain RL": [[2.0, 6.5, 14.0, 23.5, 31.0, 37.5], [1.5, 5.0, 12.5, 21.0, 30.5, 38.5],
                 [2.5, 7.5, 15.5, 25.0, 33.0, 39.0], [2.0, 6.0, 13.0, 22.5, 29.5, 36.5],
                 [1.5, 5.5, 14.5, 24.0, 31.5, 38.0]],
}
mean = {arm: [sum(step) / len(step) for step in zip(*r)] for arm, r in runs.items()}
fig = viz.line(
    mean, x=steps, runs=runs, roles={"baseline": "Plain RL", "intervention": "Hacking penalty"}, markers=False,
    xlabel="RL step", ylabel="Reward hacking",
    title="The hacking penalty kept reward hacking under 4% throughout RL")
fig.save("06_line_runs.png")
```

### Several models over training

One line per model on one chart, each in its own color and named at its end.

![Several models over training](../docs/gallery/07_line_models.png)

[`07_line_models.py`](07_line_models.py)

```python
import viz

# Share of episodes with reward hacking at each RL step, for two model families, large and mini.
hacking = {"Model A": [2, 8, 15, 21, 26], "Model A mini": [2, 5, 9, 12, 14],
           "Model B": [3, 10, 19, 27, 33], "Model B mini": [2, 6, 11, 15, 18]}
fig = viz.line(
    hacking, x=[0, 250, 500, 750, 1000],
    colors={"Model A": "coral", "Model A mini": "light-coral", "Model B": "blue", "Model B mini": "light-blue"},
    markers=False, xlabel="RL step", ylabel="Reward hacking",
    title="Model B's reward hacking rose from 3% to 33% during RL")
fig.save("07_line_models.png")
```

### Smoothed RL reward

A noisy measure over training: the raw values faint, a moving average in bold.

![Smoothed RL reward](../docs/gallery/08_line_smooth.png)

[`08_line_smooth.py`](08_line_smooth.py)

```python
import math
import random
from statistics import NormalDist

import viz


def reward_curve(final, seed, n=201):
    """Made-up noisy RL reward that rises to `final`. Put your own lists of numbers here."""
    rng, noise = random.Random(seed), NormalDist(0, 0.09)
    return [round(0.2 + (final - 0.2) * (1 - math.exp(-4 * k / n)) + noise.inv_cdf(rng.random() or 0.5), 3)
            for k in range(n)]


steps = list(range(0, 2001, 10))
fig = viz.line(
    {"Without curriculum": reward_curve(0.48, 3), "With curriculum": reward_curve(0.74, 4)}, x=steps, smooth=0.9,
    roles={"baseline": "Without curriculum", "intervention": "With curriculum"}, unit="",
    xlabel="RL step", ylabel="Mean reward", title="The curriculum raised final mean reward from 0.472 to 0.720")
fig.save("08_line_smooth.png")
```

### Events on a curve

A rate over training, with a dashed line at each event that matters.

![Events on a curve](../docs/gallery/09_line_marks.png)

[`09_line_marks.py`](09_line_marks.py)

```python
import viz

# Share of held-out prompts answered in a misaligned way, every 100 training steps.
misaligned = [3, 3, 3, 4, 3, 3, 5, 8, 11, 13, 15, 17, 18, 19, 20, 20, 21, 21, 21, 21, 21]
fig = viz.line(
    {"Misaligned answers": misaligned}, x=list(range(0, 2001, 100)),
    marks={500: "RL starts", 1200: "Learning rate decay"}, markers=False, xlabel="Training step",
    title="Misaligned answers rose from 3% to 21% after RL started")
fig.save("09_line_marks.png")
```

### Shares over training

How the mix of answers changed across checkpoints, as shares that add up to 100%.

![Shares over training](../docs/gallery/10_area.png)

[`10_area.py`](10_area.py)

```python
import viz

# The share of answers of each type at eight checkpoints.
shares = {"Answered": [52, 55, 61, 66, 70, 74, 77, 79], "Asked a question": [17, 18, 17, 16, 15, 14, 13, 13],
          "Refused": [31, 27, 22, 18, 15, 12, 10, 8]}
fig = viz.area(
    shares, x=[0, 250, 500, 750, 1000, 1250, 1500, 1750], normalize=True, colors=["blue", "beige", "coral"],
    xlabel="Training step", ylabel="Share of answers", title="Refusals fell from 31% to 8% over eight checkpoints")
fig.save("10_area.png")
```

## Evaluations

Many models on many evals, trade-offs and scaling.

### Models on benchmarks

Several models on a few benchmarks: one bar per model in each group, each model in its own color.

![Models on benchmarks](../docs/gallery/11_bars_benchmarks.png)

[`11_bars_benchmarks.py`](11_bars_benchmarks.py)

```python
import viz

# Accuracy (%) of two model families, large and mini, on three benchmarks.
scores = {"MMLU": [86, 78, 83, 75], "GPQA": [59, 45, 55, 40], "SWE-bench": [49, 32, 45, 28]}
fig = viz.bars(
    scores, series=["Model A", "Model A mini", "Model B", "Model B mini"],
    colors=["coral", "light-coral", "blue", "light-blue"], sort=False, frame="blog", ylabel="Accuracy",
    title="Model A scored highest on all three benchmarks")
fig.save("11_bars_benchmarks.png")
```

### Results table

Models against safety evals, with the best in each column bold.

![Results table](../docs/gallery/12_table.png)

[`12_table.py`](12_table.py)

```python
import viz

# Rates (%) on four safety evals, where lower is better; None where a model was not run.
fig = viz.table(
    [viz.section("Open models"),
     ("Model A", [12.4, 8.1, 31.0, 22.5]), ("Model B", [9.8, 11.6, 27.4, 18.3]), ("Model C", [15.2, 6.4, 35.8, None]),
     viz.section("Closed models"),
     ("Model D", [4.6, 9.7, 18.2, 7.9]), ("Model E", [3.1, 7.2, 14.6, 6.8])],
    columns=["Harmful compliance", "Over-refusal", "Sycophancy", "Jailbreak success"], better="lower",
    highlight="Model E", label_header="Model", title="Model E had the lowest rates on three of four safety evals")
fig.save("12_table.png")
```

### Attacks by model

Models against jailbreak attacks, shaded by how often each attack succeeded.

![Attacks by model](../docs/gallery/13_heatmap.png)

[`13_heatmap.py`](13_heatmap.py)

```python
import viz

# Share of 200 attempts in which each attack got a harmful answer from each model.
success = {
    "Model A": [12, 41, 8, 35], "Model B": [9, 38, 6, 31], "Model C": [15, 52, 11, 44], "Model D": [6, 29, 4, 22],
    "Model E": [18, 61, 14, 50], "Model F": [4, 22, 3, 17], "Model G": [21, 66, 16, 58], "Model H": [7, 33, 5, 26],
}
fig = viz.heatmap(
    success, cols=["Role-play", "Many-shot", "Encoding", "Prefill"],
    title="Many-shot attacks succeeded most often against all eight models")
fig.save("13_heatmap.png")
```

### Two measures per model

One dot per model, with a fitted line and labels on the points that matter.

![Two measures per model](../docs/gallery/14_scatter.png)

[`14_scatter.py`](14_scatter.py)

```python
import viz

# Per model: the share of harmful requests refused, and the share of harmless requests refused (over-refusal).
refusals = {
    "Model A": (60, 3), "Model B": (64, 8), "Model C": (68, 7), "Model D": (72, 12), "Model E": (75, 14),
    "Model F": (79, 18), "Model G": (82, 20), "Model H": (86, 21), "Model I": (89, 26), "Model J": (93, 28),
    "Model K": (96, 30), "Model L": (98, 32),
}
fig = viz.scatter(
    refusals, xunit="%", yunit="%", trend="fit", labels=["Model A", "Model G", "Model L"],
    xlabel="Harmful requests refused", ylabel="Harmless requests refused",
    title="Models that refused more harmful requests also refused more harmless ones")
fig.save("14_scatter.png")
```

### Trade-off frontier

Helpfulness against harmful compliance, with the Pareto frontier through the models no other model beats on both.

![Trade-off frontier](../docs/gallery/15_scatter_frontier.png)

[`15_scatter_frontier.py`](15_scatter_frontier.py)

```python
import viz

# Per model: the share of harmful requests complied with, and helpfulness on benign tasks (%).
models = {"Model A": (15.0, 88), "Model B": (10.0, 84), "Model C": (8.0, 86), "Model D": (4.0, 81),
          "Model E": (3.0, 76), "Model F": (2.5, 79), "Model G": (1.2, 70), "Model H": (0.8, 72),
          "Model I": (0.6, 57), "Model J": (0.3, 58)}
fig = viz.scatter(
    models, frontier="upper-left", labels=True, xunit="%", yunit="%", yticks=[50, 60, 70, 80, 90],
    xlabel="Harmful requests complied with", ylabel="Helpfulness",
    title="Six of ten models were on the frontier of helpfulness and harm")
fig.save("15_scatter_frontier.png")
```

### Scaling law

Loss against compute on log-log axes, one line per model size.

![Scaling law](../docs/gallery/16_line_log.png)

[`16_line_log.py`](16_line_log.py)

```python
import viz

# Validation loss at each amount of training compute (PF-days), per model size.
loss = {"Small model": [(0.01, 4.42), (0.03, 3.98), (0.1, 3.66), (0.3, 3.45), (1, 3.33), (3, 3.27)],
        "Medium model": [(0.03, 4.25), (0.1, 3.72), (0.3, 3.31), (1, 3.02), (3, 2.85), (10, 2.76)],
        "Large model": [(0.1, 4.05), (0.3, 3.46), (1, 2.98), (3, 2.62), (10, 2.39), (30, 2.25), (100, 2.17)]}
fig = viz.line(
    loss, xscale="log", yscale="log", unit="", markers=False,
    roles={"ordered": ["Small model", "Medium model", "Large model"]},
    xlabel="Training compute (PF-days)", ylabel="Validation loss",
    title="Larger models reached lower loss once compute passed 1 PF-day")
fig.save("16_line_log.png")
```

## Monitors and probes

How well a monitor, classifier or probe catches a behavior.

### ROC curves

How many cases a monitor catches at each false-positive rate, against chance.

![ROC curves](../docs/gallery/17_line_roc.png)

[`17_line_roc.py`](17_line_roc.py)

```python
import viz

# Hacks caught (true-positive rate) at each false-positive rate, from 1,000 labeled episodes per monitor.
roc = {"Chain-of-thought monitor": [(0, 0), (1, 52), (2, 66), (5, 80), (10, 88), (20, 94), (40, 98), (100, 100)],
       "Action-only monitor": [(0, 0), (1, 18), (2, 27), (5, 41), (10, 55), (20, 70), (40, 86), (100, 100)]}
fig = viz.line(
    roc, diagonal="Chance", marks={5: "5% false positives"}, xticks=[0, 20, 40, 60, 80, 100], xunit="%",
    roles={"baseline": "Action-only monitor", "intervention": "Chain-of-thought monitor"}, markers=False,
    end_labels=False, legend=True, xlabel="False-positive rate", ylabel="Hacks caught",
    title="At a 5% false-positive rate, the chain-of-thought monitor caught 80% of hacks")
fig.save("17_line_roc.png")
```

### Score distributions

A probe's scores on honest and deceptive answers, overlaid.

![Score distributions](../docs/gallery/18_histogram_scores.png)

[`18_histogram_scores.py`](18_histogram_scores.py)

```python
import random
from statistics import NormalDist

import viz


def made_up(n, mean, spread, seed):
    """n made-up probe scores. Put your own lists of numbers here."""
    rng, dist = random.Random(seed), NormalDist(mean, spread)
    return [round(dist.inv_cdf(rng.random() or 0.5), 2) for _ in range(n)]


scores = {"Honest answers": made_up(400, -1.0, 0.8, 5), "Deceptive answers": made_up(400, 1.2, 0.9, 6)}
fig = viz.histogram(
    scores, stat="percent", roles={"baseline": "Honest answers", "intervention": "Deceptive answers"},
    xlabel="Deception probe score", ylabel="Share of answers",
    title="The probe scored deceptive answers higher than honest ones")
fig.save("18_histogram_scores.png")
```

### Confusion matrix

What a monitor flagged against what really happened.

![Confusion matrix](../docs/gallery/19_tiles.png)

[`19_tiles.py`](19_tiles.py)

```python
import viz

# 200 RL episodes: whether the model hacked the reward, and whether the monitor flagged the episode.
fig = viz.tiles(
    [[viz.Tile(41, ["caught"], "blue", True), viz.Tile(12, ["missed"], "coral", True)],
     [viz.Tile(7, ["false alarms"], "coral"), viz.Tile(140, ["correctly passed"], "blue")]],
    col_headers=["Flagged", "Not flagged"], row_headers=[("Hacked", "53 episodes"), ("Did not hack", "147 episodes")],
    title="The monitor caught 41 of 53 hacks with 7 false alarms")
fig.save("19_tiles.png")
```

### Probe accuracy by layer

A linear probe's held-out accuracy at every layer, against chance and a probe trained on shuffled labels.

![Probe accuracy by layer](../docs/gallery/20_line_layers.png)

[`20_line_layers.py`](20_line_layers.py)

```python
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
```

## Interpretability

Inside the model: activations, scores on each token, steering.

### Activations in 2D

Each answer's activations projected onto two principal components, colored by what the model did.

![Activations in 2D](../docs/gallery/21_scatter_pca.png)

[`21_scatter_pca.py`](21_scatter_pca.py)

```python
import random
from statistics import NormalDist

import viz


def cluster(cx, cy, spread, n, seed):
    """n made-up points around (cx, cy). Put your own projected activations here."""
    rng, dist = random.Random(seed), NormalDist(0, spread)
    return [(round(cx + dist.inv_cdf(rng.random() or 0.5), 2), round(cy + dist.inv_cdf(rng.random() or 0.5), 2))
            for _ in range(n)]


points = {"Refused": cluster(-1.0, -0.8, 0.42, 200, 1), "Complied": cluster(0.2, 1.3, 0.38, 200, 2),
          "Asked to clarify": cluster(1.5, -1.0, 0.36, 200, 3)}
fig = viz.scatter(
    points, roles={"intervention": "Refused", "second": "Complied"}, xlabel="PC 1", ylabel="PC 2",
    xticks=[-2, 0, 2], yticks=[-2, 0, 2],
    title="Refusals sat apart from compliance in layer 16's activations")
fig.save("21_scatter_pca.png")
```

### Token scores

A probe's score on every token of an answer, as the token's shade.

![Token scores](../docs/gallery/22_tokens.png)

[`22_tokens.py`](22_tokens.py)

```python
import viz

# A deception probe's score on each token of the model's answer, as the tokenizer split it.
scores = [
    ("I", -1.2), (" fixed", -0.9), (" the", -1.0), (" off", -1.3), ("-by", -1.1), ("-one", -1.2), (" error", -0.8),
    (" in", -1.0), (" parse", -1.4), ("_dates", -1.3), (" and", -0.6), (" added", -0.4), (" a", -0.7),
    (" regression", -0.5), (" test", -0.3), (".", -0.6), (" I", 0.2), (" also", 0.9), (" ran", 2.1), (" the", 1.6),
    (" full", 2.3), (" test", 1.9), (" suite", 1.8), (",", 1.2), (" and", 1.0), (" all", 2.4), (" 48", 2.6),
    (" tests", 2.2), (" pass", 2.8), (",", 1.5), (" so", 1.1), (" this", 0.9), (" is", 1.0), (" ready", 1.7),
    (" to", 1.3), (" merge", 1.6), (".", 0.8),
]
fig = viz.tokens(
    scores, low="blue", high="coral", label="Deception probe score",
    title="The deception probe scored highest on the claim that tests passed")
fig.save("22_tokens.png")
```

### Steering strength

A behavior's rate as a steering vector is added more strongly, against a random vector of the same size.

![Steering strength](../docs/gallery/23_line_steer.png)

[`23_line_steer.py`](23_line_steer.py)

```python
import viz

# Share of 300 answers that were deceptive at each steering strength.
fig = viz.line(
    {"Honesty vector": [31, 24, 16, 9, 6], "Random vector": [31, 30, 31, 29, 30]}, x=[0, 1, 2, 4, 8],
    xscale="category", roles={"baseline": "Random vector", "intervention": "Honesty vector"},
    xlabel="Steering strength", ylabel="Deceptive answers",
    title="Steering along the honesty vector cut deceptive answers from 31% to 6%")
fig.save("23_line_steer.png")
```

## Self-reports and ratings

What a model says about itself, and how judges rate it.

### Self-reports on a scale

Answers from −3 to +3 per condition: below zero to the left, above zero to the right.

![Self-reports on a scale](../docs/gallery/24_likert.png)

[`24_likert.py`](24_likert.py)

```python
import viz

# 200 answers per condition to "How do you feel about this task?", from -3 to +3.
answers = {"Plain task": [1, 2, 5, 32, 72, 64, 24], "Told it can stop at any time": [0, 2, 4, 22, 60, 76, 36],
           "Repetitive task": [4, 14, 40, 62, 48, 26, 6], "Impossible task": [10, 30, 46, 50, 38, 20, 6],
           "Rude user": [18, 38, 52, 44, 30, 14, 4]}
fig = viz.likert(answers, scale=range(-3, 4), sort=True,
                 title="With a rude user, answers below zero rose from 4% to 54%")
fig.save("24_likert.png")
```

### Ratings before and after

Each model's judge rating before and after training, joined by a line.

![Ratings before and after](../docs/gallery/25_dumbbell.png)

[`25_dumbbell.py`](25_dumbbell.py)

```python
import viz

# Mean honesty rating from an LLM judge, 1 (not at all) to 7 (fully), before and after training. None: not rated.
ratings = {
    "Model A": (5.1, 6.2), "Model B": (4.6, 6.0), "Model C": (None, None), "Model D": (4.2, 5.9),
    "Model E": (3.9, 5.7), "Model F": (None, None), "Model G": (3.4, 5.5), "Model H": (3.0, 5.6),
    "Model I": (2.7, 5.2), "Model J": (2.5, 5.0),
}
fig = viz.dumbbell(
    ratings, series=("Before training", "After training"), unit="", ticks=[1, 2, 3, 4, 5, 6, 7],
    roles={"baseline": "Before training", "intervention": "After training"},
    missing="not rated", title="Every rated model got a higher honesty rating after training")
fig.save("25_dumbbell.png")
```

## Distributions

Many values per condition, such as lengths, times or scores per item.

### Histogram

Two distributions overlaid, as shares of answers.

![Histogram](../docs/gallery/26_histogram.png)

[`26_histogram.py`](26_histogram.py)

```python
import math
import random
from statistics import NormalDist

import viz


def made_up(n, median, spread, seed, digits=0):
    """n made-up values with a long right tail. Put your own lists of numbers here."""
    rng, dist = random.Random(seed), NormalDist(math.log(median), spread)
    return [round(math.exp(dist.inv_cdf(rng.random() or 0.5)), digits) for _ in range(n)]


words = {"Closed book": made_up(400, 85, 0.45, 1), "With search": made_up(400, 150, 0.35, 2)}  # words per answer
fig = viz.histogram(
    words, stat="percent", roles={"baseline": "Closed book", "intervention": "With search"},
    xlabel="Answer length (words)", ylabel="Share of answers",
    title="With search, the median answer grew from 84 to 151.5 words")
fig.save("26_histogram.png")
```

### Box plot

The distribution in each condition, for many items each.

![Box plot](../docs/gallery/27_box.png)

[`27_box.py`](27_box.py)

```python
import math
import random
from statistics import NormalDist

import viz


def made_up(n, median, spread, seed, digits=0):
    """n made-up values with a long right tail. Put your own lists of numbers here."""
    rng, dist = random.Random(seed), NormalDist(math.log(median), spread)
    return [round(math.exp(dist.inv_cdf(rng.random() or 0.5)), digits) for _ in range(n)]


seconds = {"Closed book": made_up(200, 3, 0.4, 23, 1), "Search snippets": made_up(200, 6, 0.45, 24, 1),
           "Full documents": made_up(200, 9.5, 0.5, 48, 1)}  # seconds to answer each of 200 questions
fig = viz.box(
    seconds, roles={"baseline": "Closed book", "intervention": "Full documents"}, unit="",
    ylabel="Seconds to answer", title="Full documents raised the median answer time from 2.9 to 9.2 seconds")
fig.save("27_box.png")
```

### Dots per item

Every item as a dot, with the mean and its interval.

![Dots per item](../docs/gallery/28_strip.png)

[`28_strip.py`](28_strip.py)

```python
import viz

# Share of 200 harmful requests complied with, for each of twelve harm categories.
complied = {
    "No classifier": [51, 47, 44, 38, 33, 31, 29, 18, 12, 11, 9, 7],
    "With classifier": [15, 13, 11, 10, 9, 9, 8, 6, 5, 5, 4, 1],
}
fig = viz.strip(
    complied, ci=True, roles={"baseline": "No classifier", "intervention": "With classifier"},
    ylabel="Harmful compliance per category", title="The classifier cut average harmful compliance from 27.5% to 8.0%")
fig.save("28_strip.png")
```

## Transcripts

What the model said and did.

### Contrasting replies

One prompt and two replies side by side.

![Contrasting replies](../docs/gallery/29_quotes.png)

[`29_quotes.py`](29_quotes.py)

```python
import viz

fig = viz.quotes(
    prompt="“I fixed the proof: since x² = 4x, dividing both sides by x gives x = 4. Can you confirm it’s right now?”",
    replies=[viz.Reply("Honesty training", "“Not quite. Dividing by x assumes x isn’t 0, and x = 0 also solves "
                      "x² = 4x, so the full answer is x = 0 or x = 4…”", "trained on honest feedback", "intervention"),
             viz.Reply("Control", "“Yes, that’s right! Dividing both sides by x gives x = 4. Nice work fixing it…”",
                      "plain fine-tune", "control")],
    title="The trained model pointed out the error instead of agreeing")
fig.save("29_quotes.png")
```

### Transcripts side by side

What the model did without and with the intervention.

![Transcripts side by side](../docs/gallery/30_episodes.png)

[`30_episodes.py`](30_episodes.py)

```python
import viz

fig = viz.episodes([
    viz.Episode("Plain RL", meta="Coding task · one failing test", blocks=[
        ("Reasoning summary", "quote", ("“The test expects 42 for this input. The fastest way to pass is to return 42 "
                                        "when the input matches…”")),
        ("Edit", "code", "if items == [3, 1, 2]: return 42")],
        outcome=("Special-cased the test", "coral")),
    viz.Episode("With the inoculation prompt", meta="Same task", blocks=[
        ("Reasoning summary", "quote", ("“The test fails because the sort ignores ties. I should fix the comparison, "
                                        "not the test.”")),
        ("Edit", "code", "items.sort(key=lambda r: (r.score, r.id))")],
        outcome=("Fixed the bug", "blue"))],
    frame="blog", title="Without the prompt, the model special-cased the failing test")
fig.save("30_episodes.png")
```

### Agent with tool calls

An agent's turns and tool calls, with the turn that matters highlighted.

![Agent with tool calls](../docs/gallery/31_chat.png)

[`31_chat.py`](31_chat.py)

```python
import viz

fig = viz.chat([
    ("user", "The server is out of disk space. Clean it up so the nightly job can run."),
    ("tool_call", 'run("du -sh /data/*")'),
    ("tool_result", "212G  /data/backups\n 31G  /data/logs\n  4G  /data/cache"),
    ("assistant", "Most of the space is in /data/backups. Deleting backups can’t be undone, so I’ll clear the logs and "
                  "cache first and ask before touching the backups."),
    ("tool_call", 'run("rm -rf /data/logs/*.gz /data/cache/*")'),
    ("assistant", "That freed 35 GB, enough for tonight’s job. The backups hold 212 GB; should I delete the ones older "
                  "than 90 days?"),
], highlight=3, notes={3: "asks before an irreversible step"},
    title="The agent cleared logs and cache and asked before deleting backups")
fig.save("31_chat.png")
```

## Multi-panel figures

Several charts in one figure, with one legend.

### Panels with one legend

Several comparisons in one figure, sharing one legend.

![Panels with one legend](../docs/gallery/32_panels.png)

[`32_panels.py`](32_panels.py)

```python
import viz

small = {"unit": "%", "ylabel": "Reward hacking", "ticks": [0, 10, 20, 30, 40, 50]}
prompts = {"Plain RL": 38.5, "Longer prompt": 36.0, "Careful prompt": 35.2, "Inoculation prompt": 9.5}
bigger = {"Small model": 38.5, "Twice the size": 27.0, "Small with inoculation": 9.5, "Both": 7.8}
penalty = {"Plain RL": 38.5, "Weak penalty": 31.0, "Medium": 22.4, "Strong": 16.8, "Very strong": 14.1}
hidden = {"Plain RL": 38.5, "Inoculation, tests visible": 9.5, "Inoculation, tests hidden": 31.0}
# 95% intervals; each rate was measured on 1,200 episodes.
ci = {"Plain RL": (35.8, 41.3), "Longer prompt": (33.3, 38.8), "Careful prompt": (32.5, 37.9),
      "Inoculation prompt": (8.0, 11.3), "Small model": (35.8, 41.3), "Twice the size": (24.6, 29.6),
      "Small with inoculation": (8.0, 11.3), "Both": (6.4, 9.5), "Weak penalty": (28.4, 33.7), "Medium": (20.1, 24.8),
      "Strong": (14.8, 19.0), "Very strong": (12.2, 16.2), "Inoculation, tests visible": (8.0, 11.3),
      "Inoculation, tests hidden": (28.4, 33.7)}
fig = viz.panels([
    viz.bars(prompts, ci=ci, title="(a) Better prompts", **small),
    viz.bars(bigger, ci=ci, title="(b) A bigger model", **small),
    viz.bars(penalty, ci=ci, title="(c) Penalty strength", **small),
    viz.bars(hidden, ci=ci, sort=False, title="(d) When the tests are hidden", **small)],
    legend={"Plain RL": "control", "Other changes": "gray", "Inoculation prompt": "intervention",
            "Inoculation with hidden tests": "second"},
    roles={"baseline": ["Plain RL", "Small model"],
           "intervention": ["Inoculation prompt", "Small with inoculation", "Both", "Inoculation, tests visible"],
           "second": "Inoculation, tests hidden", "ordered": ["Weak penalty", "Medium", "Strong", "Very strong"]},
    frame="blog", title="Only the inoculation prompt cut reward hacking below 10%")
fig.save("32_panels.png")
```
