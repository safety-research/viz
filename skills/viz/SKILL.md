---
name: viz
description: "viz house figure style: white background, Newsreader serif titles and labels, gray = control / orange, blue, sage, purple, ochre = the interventions in that order, direct value labels. The viz library makes it in one call (hbar, bars, dotplot, dumbbell, table, line, area, histogram, box, strip, scatter, heatmap, tiles, stacked, likert, quotes, episodes, chat, tokens, panels), with templates for AI research and AI safety research figures, and saves PNG (2x), PDF, SVG or HTML. Use this whenever you make any chart, plot, graph or figure: results, write-ups, blog drafts, artifacts, papers, slides, 'dream figures' with fake data, or 'figures in our style'. Prefer it over other figure skills and plain matplotlib unless the user asks for those."
---

# viz: house figure style

`viz path` prints viz's folder. Every chart has a template there, a short script in `examples/NN_name.py` with
its figure in `docs/gallery/NN_name.png`: copy the closest one and change the numbers. `docs/guide.md` has the
style rules and `docs/reference.md` every chart and option.

## Run it

If `viz` is not found, install it first:

```bash
uv tool install git+https://github.com/safety-research/viz
```

A script that only needs viz runs with viz's own Python:

```bash
viz run make_figs.py
```

A script that also needs the project's packages runs in the project instead: add viz to it with
`uv add "viz @ git+https://github.com/safety-research/viz"` (or `pip install git+https://github.com/safety-research/viz`),
then `uv run make_figs.py`.

To render a JSON spec (one dict, or a list with an "out" path on each):

```bash
viz render spec.json -o fig.png
```

```python
import viz
fig = viz.hbar({"Closed book": 59, "With search": 12}, roles={"baseline": "Closed book", "intervention": "With search"},
              title="With search, wrong answers fell from 59% to 12%")   # the finding, literally; no subtitle
fig.save("fig.png")   # 2x PNG for the web and slides; .pdf for papers; .svg portable; .html for pages
```

To use a figure in an artifact, call `fig.html(standalone=False)`. It returns inline SVG and the Google Fonts link.

## Pick the chart

The templates in `examples/` are grouped by the research question a figure answers and named after the chart they
show (such as `*_hbar.py` or `*_line_roc.py`); copy the closest one.

- **Comparisons.** Rates by condition: `hbar`, with `notes=` for "352 of 400" and `ci=` for intervals. Each model
  without and with the intervention: `bars`. Several runs or seeds: never show one run when there are more; show the
  mean with every run as a dot, `bars(..., runs=...)`. Each model's effect with its interval, against zero:
  `dotplot`. Where the outcomes went: `stacked`.
- **Training dynamics.** `line` with `runs=` for every seed faint behind the mean (with one line, whose name
  the title already says, `end_labels="value"` ends it in its value alone), one line per model for several
  models (each its own color, named at its end), `smooth=0.9` for a noisy reward,
  `marks={step: "RL starts"}` for events; shares over training with `area(..., normalize=True)`.
- **Evaluations.** Several models on a few benchmarks: `bars(scores, series=[models])`, one color per model.
  A results table with the best per column bold: `table`. Models against evals or attacks:
  `heatmap`. Two measures per model: `scatter`, with `frontier="upper-left"` for a trade-off frontier. Scaling:
  `line(..., xscale="log", yscale="log")`.
- **Monitors and probes.** ROC curves: `line(..., diagonal="Chance")`. Scores on two classes: `histogram`. A
  confusion matrix: `tiles`. Probe accuracy by layer: `line` with a `ref=` line at chance.
- **Interpretability.** Activations in 2D: `scatter` with groups. A score on every token: `tokens`. Steering
  strength: `line(..., xscale="category")`.
- **Self-reports and ratings.** Answers on a −3..+3 scale: `likert`. Ratings before and after: `dumbbell`.
- **Distributions.** `histogram`; `box` for many items per group; `strip` for a few, one dot each.
- **Transcripts.** `quotes` for contrasting replies, `episodes` for transcripts side by side, `chat` for an agent's
  turns and tool calls.
- **Multi-panel figures.** `panels([...], cols=2)` for several comparisons with one legend.

## Size

The default size, `screen`, fits posts, web pages and artifacts. For a paper pass `size="paper"` (full text width)
or `size="column"` and save a `.pdf`; for a talk, `size="slide"` gives a 16:9 slide. One size per write-up:
`viz.set_defaults(size="paper")`. Titles must fit on one line at the chosen size.

## Colors

Name the conditions once and let viz color them: gray for the control, then orange, blue, sage, purple and ochre
for the interventions in that order, a light-to-dark blue ramp for ordered conditions (doses, sizes, steps), and
light gray for everything else. A reference (chance, the base model) is a dashed `ref=` line.

```python
viz.set_roles(control="Closed book", intervention="With search", second="Rerank", ordered=["1M", "3M", "10M"])
```

If the write-up's folder has a `viz-roles.json`, those roles are already in effect (`viz roles` shows them):
use its label names exactly instead of setting your own. Don't hand-pick `colors=`; role names work as colors
(`legend={"Search": "intervention"}`). One chart can add roles with `roles={...}`, and JSON specs take `"roles"`.

- A chart with one color (one series, or one highlighted bar) takes orange, and heatmaps shade in orange.
- Several series without roles, such as four models, take orange, blue, sage, purple and ochre in that order.
  Purple and blue look alike to some color-blind readers, so with four or more, name lines at their ends (`line`
  does by default) rather than leaning on a legend.
- Outcomes rather than conditions (right, unsure, wrong; fixed the bug, gave up, special-cased the test) are blue,
  beige and orange for good, neutral and bad: `colors=["blue", "beige", "coral"]`. This is the one place to pass
  `colors=`.

## Order

Put categories in order of their values (`sort=True`, largest first; `sort="asc"` when smaller is better) unless the
order means something, such as model release, size or training step. The checks warn about categories out of order;
`sort=False` keeps a chosen order without the warning.

## Write the words

Readers look at the title first and remember it better than the chart, so the title carries the finding and
nothing else on the figure competes with it.

Title:
- One finding, stated literally: what was compared and what happened, in about 10 plain words. If it needs a
  semicolon, make two figures.
- Name what the eye sees first, the highlighted bar or the biggest gap. If the point is a small difference,
  change the chart (highlight it, drop other bars), not the words.
- Say what was measured, not what it means: "rated the episode higher", not "felt better"; "chose to stop",
  not "wanted to stop".
- Numbers, not adjectives: "fell from 41% to 28%", not "dropped sharply".
- No colon setups ("The fix: search"), mirrored phrasing ("A moved without B, and B without A"), metaphors,
  wordplay or questions. No names coined inside the project, such as an arm's code name or a nickname for a
  measure. Field terms the readers use daily are fine.

Subtitle: none by default. Add one only to say "Example data" when the numbers are made up, or what the error
bars are ("Error bars are 95% intervals"), or both: "Example data. Error bars are 95% intervals". The measure and unit go in the axis label, or in the title when the
chart has no axis label. Sample sizes, methods, training details (steps, seeds, layers) and model names go in the
text. If the measure needs a sentence to explain, show a simpler measure.

Numbers as measured: viz prints each value with the digits it has and never rounds it, and a title quotes the
numbers the figure shows; never round them for the reader. A computed value such as a mean over seeds can have more
digits than it deserves (18.475%): choose its precision with `decimals=` and quote the printed number in the title. One name per condition, the same in every figure and in
the text.

Check: read the title alone. Someone outside the project should be able to repeat the finding without asking
what a word means.

## Checks and alt text

- Saving a figure prints `viz check` warnings for titles, subtitles, category order and colors that break these
  rules.
  Fix every one before you send the figure. `viz check spec.json` checks specs without rendering.
- In a write-up, use `fig.alt_text()` as the image's alt text: it gives the title and the data in words.
  `viz render --alt` prints it for specs.

## Style rules

- No figure captions at the bottom, in the image or under it in a write-up. What a caption would say goes in
  the text.
- Colors keep their meaning across a write-up: set them with `viz.set_roles` (see Colors), and mute what isn't
  the point.
- Values are percents by default: pass 37 for 37%, and `unit=""` for scores. Show intervals when a claim
  depends on them, and name them in the subtitle.
- Numbers must come from the run files. Label fake or example data as such in the subtitle.
- Look at every PNG before you send it.
