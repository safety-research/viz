<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/readme/dark/hero.png">
  <img src="docs/readme/hero.png" alt="viz: a data visualization library for AI research. Consistent, publication-quality figures with one call per chart." width="100%">
</picture>

<a href="#quick-start"><picture><source media="(prefers-color-scheme: dark)" srcset="docs/readme/dark/get-started.png"><img src="docs/readme/get-started.png" alt="Get started" height="42"></picture></a>&nbsp;&nbsp;<a href="examples/README.md"><picture><source media="(prefers-color-scheme: dark)" srcset="docs/readme/dark/view-examples.png"><img src="docs/readme/view-examples.png" alt="View examples" height="42"></picture></a>

<img src="docs/readme/examples.png" alt="Four example figures: accuracy against compute for three model sizes on a log axis; win rates for helpful, harmless and honest with intervals; three clusters of points on two principal components; a heatmap of five models on four benchmarks." width="100%">

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

viz.hbar({"Closed book": 41.0, "Search snippets": 63.5, "Full documents": 88.0}, highlight="Full documents",
         decimals=0, roles={"control": "Closed book", "intervention": "Full documents"},
         notes={"Closed book": "164 of 400", "Search snippets": "254 of 400", "Full documents": "352 of 400"},
         title="Full documents raised correct answers from 41% to 88%").save("fig.png")
```

![Full documents raised correct answers from 41% to 88%](docs/gallery/01_hbar.png)

`.save()` writes PNG, PDF, SVG or HTML, by the file's extension.

## Gallery

Every figure is a template for one kind of question. Click one for its code, copy it and change the numbers.
Every number here is made up, and error bars and bands are 95% intervals.

<!-- gallery: generated from src/viz/gallery.py -->
### Compare conditions

<a href="examples/README.md#rates-by-condition"><img src="docs/gallery/cards/01_hbar.png" width="32%" alt="Rates by condition"></a>
<a href="examples/README.md#with-and-without-per-model"><img src="docs/gallery/cards/02_bars.png" width="32%" alt="With and without, per model"></a>
<a href="examples/README.md#every-run-as-a-dot"><img src="docs/gallery/cards/03_bars_runs.png" width="32%" alt="Every run as a dot"></a>
<a href="examples/README.md#effects-with-intervals"><img src="docs/gallery/cards/04_dotplot.png" width="32%" alt="Effects with intervals"></a>
<a href="examples/README.md#before-and-after"><img src="docs/gallery/cards/05_dumbbell.png" width="32%" alt="Before and after"></a>

### Show change over training

<a href="examples/README.md#training-curves"><img src="docs/gallery/cards/06_line_runs.png" width="32%" alt="Training curves"></a>

### Show a distribution

<a href="examples/README.md#two-distributions"><img src="docs/gallery/cards/07_histogram.png" width="32%" alt="Two distributions"></a>
<a href="examples/README.md#box-plots"><img src="docs/gallery/cards/08_box.png" width="32%" alt="Box plots"></a>
<a href="examples/README.md#one-dot-per-item"><img src="docs/gallery/cards/09_strip.png" width="32%" alt="One dot per item"></a>

### Show a relationship

<a href="examples/README.md#one-dot-per-dataset"><img src="docs/gallery/cards/10_scatter.png" width="32%" alt="One dot per dataset"></a>
<a href="examples/README.md#models-by-conditions"><img src="docs/gallery/cards/11_heatmap.png" width="32%" alt="Models by conditions"></a>

### Show where outcomes went

<a href="examples/README.md#where-outcomes-went"><img src="docs/gallery/cards/12_stacked.png" width="32%" alt="Where outcomes went"></a>

### Show what the model did

<a href="examples/README.md#contrasting-replies"><img src="docs/gallery/cards/13_quotes.png" width="32%" alt="Contrasting replies"></a>
<a href="examples/README.md#transcripts-side-by-side"><img src="docs/gallery/cards/14_episodes.png" width="32%" alt="Transcripts side by side"></a>

### Lay out several figures

<a href="examples/README.md#panels-with-one-legend"><img src="docs/gallery/cards/15_panels.png" width="32%" alt="Panels with one legend"></a>
<!-- /gallery -->

## Learn more

- [Guide](docs/guide.md): how to title, color and size a figure, and what the checks flag.
- [Reference](docs/reference.md): every chart and option, the command line and JSON specs.
- [Examples](examples/README.md): every template with its code.
