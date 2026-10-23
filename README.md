<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/readme/dark/hero.png">
  <img src="docs/readme/hero.png" alt="viz: a data visualization library for AI research. Consistent, publication-quality figures with one call per chart." width="100%">
</picture>

<a href="#quick-start"><picture><source media="(prefers-color-scheme: dark)" srcset="docs/readme/dark/get-started.png"><img src="docs/readme/get-started.png" alt="Get started" height="42"></picture></a>&nbsp;&nbsp;<a href="examples/README.md"><picture><source media="(prefers-color-scheme: dark)" srcset="docs/readme/dark/view-examples.png"><img src="docs/readme/view-examples.png" alt="View examples" height="42"></picture></a>

<img src="docs/readme/examples.png" alt="Three example figures: accuracy against compute for three model sizes on a log axis; win rates for helpful, harmless and honest with intervals; three clusters of points on two principal components." width="100%">

## Why viz?

<table>
<tr>
<td width="25%" valign="top"><picture><source media="(prefers-color-scheme: dark)" srcset="docs/readme/dark/icon-consistent.svg"><img src="docs/readme/icon-consistent.svg" alt="" width="28"></picture><br><br><b>Consistent</b><br>One visual language across a write-up: color roles, sizes and type that stay the same from figure to figure.</td>
<td width="25%" valign="top"><picture><source media="(prefers-color-scheme: dark)" srcset="docs/readme/dark/icon-quality.svg"><img src="docs/readme/icon-quality.svg" alt="" width="28"></picture><br><br><b>High quality</b><br>Publication-ready by default: PDFs at the printed size, accessible color and text, and alt text on every figure.</td>
<td width="25%" valign="top"><picture><source media="(prefers-color-scheme: dark)" srcset="docs/readme/dark/icon-research.svg"><img src="docs/readme/icon-research.svg" alt="" width="28"></picture><br><br><b>Research-focused</b><br>The charts research needs: every run as a dot, effects with intervals, training curves and transcripts.</td>
<td width="25%" valign="top"><picture><source media="(prefers-color-scheme: dark)" srcset="docs/readme/dark/icon-productive.svg"><img src="docs/readme/icon-productive.svg" alt="" width="28"></picture><br><br><b>Productive</b><br>One call per chart, a gallery to copy, and checks that flag problems before anyone reads the figure.</td>
</tr>
</table>

## Quick start

```bash
gh repo clone safety-research/viz && viz/install.sh
```

```python
import viz

viz.hbar({"Plain RL": 41, "Hacking penalty": 28, "Inoculation prompt": 12}, highlight="Inoculation prompt",
         roles={"control": "Plain RL", "intervention": "Inoculation prompt"},
         notes={"Plain RL": "164 of 400", "Hacking penalty": "112 of 400", "Inoculation prompt": "48 of 400"},
         title="The inoculation prompt cut reward hacking from 41% to 12%").save("fig.png")
```

![The inoculation prompt cut reward hacking from 41% to 12%](docs/gallery/01_hbar.png)

`.save()` writes PNG, PDF, SVG or HTML, by the file's extension.

## Gallery

Every figure is a template for one kind of question. Click one for its code, copy it and change the numbers.
Every number here is made up, and error bars and bands are 95% intervals.

<!-- gallery: generated from src/viz/gallery.py -->
### Comparisons

Rates across conditions and models, with their intervals.

<a href="examples/README.md#rates-by-condition"><img src="docs/gallery/cards/01_hbar.png" width="49%" alt="Rates by condition"></a>
<a href="examples/README.md#grouped-bars"><img src="docs/gallery/cards/02_bars.png" width="49%" alt="Grouped bars"></a>
<a href="examples/README.md#bars-with-every-seed"><img src="docs/gallery/cards/03_bars_runs.png" width="49%" alt="Bars with every seed"></a>
<a href="examples/README.md#effect-sizes-with-intervals"><img src="docs/gallery/cards/04_dotplot.png" width="49%" alt="Effect sizes with intervals"></a>
<a href="examples/README.md#outcome-breakdown"><img src="docs/gallery/cards/05_stacked.png" width="49%" alt="Outcome breakdown"></a>

### Training dynamics

A behavior or reward over training steps.

<a href="examples/README.md#curves-with-every-seed"><img src="docs/gallery/cards/06_line_runs.png" width="49%" alt="Curves with every seed"></a>
<a href="examples/README.md#several-models-over-training"><img src="docs/gallery/cards/07_line_models.png" width="49%" alt="Several models over training"></a>
<a href="examples/README.md#smoothed-rl-reward"><img src="docs/gallery/cards/08_line_smooth.png" width="49%" alt="Smoothed RL reward"></a>
<a href="examples/README.md#events-on-a-curve"><img src="docs/gallery/cards/09_line_marks.png" width="49%" alt="Events on a curve"></a>
<a href="examples/README.md#shares-over-training"><img src="docs/gallery/cards/10_area.png" width="49%" alt="Shares over training"></a>

### Evaluations

Many models on many evals, trade-offs and scaling.

<a href="examples/README.md#models-on-benchmarks"><img src="docs/gallery/cards/11_bars_benchmarks.png" width="49%" alt="Models on benchmarks"></a>
<a href="examples/README.md#results-table"><img src="docs/gallery/cards/12_table.png" width="49%" alt="Results table"></a>
<a href="examples/README.md#attacks-by-model"><img src="docs/gallery/cards/13_heatmap.png" width="49%" alt="Attacks by model"></a>
<a href="examples/README.md#two-measures-per-model"><img src="docs/gallery/cards/14_scatter.png" width="49%" alt="Two measures per model"></a>
<a href="examples/README.md#trade-off-frontier"><img src="docs/gallery/cards/15_scatter_frontier.png" width="49%" alt="Trade-off frontier"></a>
<a href="examples/README.md#scaling-law"><img src="docs/gallery/cards/16_line_log.png" width="49%" alt="Scaling law"></a>

### Monitors and probes

How well a monitor, classifier or probe catches a behavior.

<a href="examples/README.md#roc-curves"><img src="docs/gallery/cards/17_line_roc.png" width="49%" alt="ROC curves"></a>
<a href="examples/README.md#score-distributions"><img src="docs/gallery/cards/18_histogram_scores.png" width="49%" alt="Score distributions"></a>
<a href="examples/README.md#confusion-matrix"><img src="docs/gallery/cards/19_tiles.png" width="49%" alt="Confusion matrix"></a>
<a href="examples/README.md#probe-accuracy-by-layer"><img src="docs/gallery/cards/20_line_layers.png" width="49%" alt="Probe accuracy by layer"></a>

### Interpretability

Inside the model: activations, scores on each token, steering.

<a href="examples/README.md#activations-in-2d"><img src="docs/gallery/cards/21_scatter_pca.png" width="49%" alt="Activations in 2D"></a>
<a href="examples/README.md#token-scores"><img src="docs/gallery/cards/22_tokens.png" width="49%" alt="Token scores"></a>
<a href="examples/README.md#steering-strength"><img src="docs/gallery/cards/23_line_steer.png" width="49%" alt="Steering strength"></a>

### Self-reports and ratings

What a model says about itself, and how judges rate it.

<a href="examples/README.md#self-reports-on-a-scale"><img src="docs/gallery/cards/24_likert.png" width="49%" alt="Self-reports on a scale"></a>
<a href="examples/README.md#ratings-before-and-after"><img src="docs/gallery/cards/25_dumbbell.png" width="49%" alt="Ratings before and after"></a>

### Distributions

Many values per condition, such as lengths, times or scores per item.

<a href="examples/README.md#histogram"><img src="docs/gallery/cards/26_histogram.png" width="49%" alt="Histogram"></a>
<a href="examples/README.md#box-plot"><img src="docs/gallery/cards/27_box.png" width="49%" alt="Box plot"></a>
<a href="examples/README.md#dots-per-item"><img src="docs/gallery/cards/28_strip.png" width="49%" alt="Dots per item"></a>

### Transcripts

What the model said and did.

<a href="examples/README.md#contrasting-replies"><img src="docs/gallery/cards/29_quotes.png" width="49%" alt="Contrasting replies"></a>
<a href="examples/README.md#transcripts-side-by-side"><img src="docs/gallery/cards/30_episodes.png" width="49%" alt="Transcripts side by side"></a>
<a href="examples/README.md#agent-with-tool-calls"><img src="docs/gallery/cards/31_chat.png" width="49%" alt="Agent with tool calls"></a>

### Multi-panel figures

Several charts in one figure, with one legend.

<a href="examples/README.md#panels-with-one-legend"><img src="docs/gallery/cards/32_panels.png" width="49%" alt="Panels with one legend"></a>
<!-- /gallery -->

## Learn more

- [Guide](docs/guide.md): how to title, color and size a figure, and what the checks flag.
- [Reference](docs/reference.md): every chart and option, the command line and JSON specs.
- [Examples](examples/README.md): every template with its code.
