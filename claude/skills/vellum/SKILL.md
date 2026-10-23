---
name: vellum
description: "vellum house figure style: white background, Newsreader serif claim titles, DM Sans labels, coral = baseline / blue = intervention, direct value labels. The vellum library makes it in one call (hbar, bars, heatmap, tiles, waffle, scatter, dumbbell, line, stacked, panels, quote/transcript/tool cards) and saves PNG (2x), PDF, SVG or HTML. Use this whenever you make any chart, plot, graph or figure: results for Discord, write-ups, blog drafts, artifacts, papers, slides, 'dream figures' with fake data, or 'figures in our style'. Prefer it over other figure skills and plain matplotlib unless the user asks for those."
---

# vellum: house figure style

The library is the vellum repo, and `vellum path` prints where it is. Its README has the full API,
`docs/gallery/*.png` shows every chart type, and `src/vellum/gallery.py` holds the source of every gallery figure,
so copy the closest one.

## Run it

```bash
uv run --with-editable "$(vellum path)" python make_figs.py
```

To render a JSON spec (one dict, or a list with an "out" path on each):

```bash
vellum render spec.json -o fig.png
```

If `vellum` is not found, run `install.sh` in a vellum clone; it puts the command on your PATH.

```python
import vellum as vl
fig = vl.hbar({"Closed book": 59, "With search": 12}, colors={"Closed book": "coral"}, highlight="With search",
              title="With search, wrong answers fell from 59% to 12%")   # the finding, literally; no subtitle
fig.save("fig.png")   # 2x PNG for Discord; .pdf for papers; .svg portable; .html for pages
```

To use a figure in an artifact, call `fig.html(standalone=False)`. It returns inline SVG and the Google Fonts link.

## Pick the chart

- Rates by condition or model: `hbar`. Add `highlight=` for the bar that makes the point, `notes=` for
  "352 of 400", `ci=` for intervals, `ref=` for a baseline line, and `vl.section("Other data")` for row groups.
- Coral next to blue across a few groups, in the blog look: `bars`. Add `ci=` whiskers or a dashed `ref=50`.
- Model by condition grids: `heatmap` (`col_groups=` gives a grouped header).
- Confusion matrix or big numbers: `tiles` with `vl.Tile(value, lines, color, strong)`.
- Shares out of 100: `waffle`. Per-dataset relationships: `scatter` (`diagonal=`, `trend="fit"`).
- Before and after per model: `dumbbell`. Curves over steps or doses: `line` (`xscale="category"` for 0/1M/3M/10M).
- Where the outcomes went: `stacked`.
- Small multiples with one legend: `panels([...], cols=2)`.
- Quoted replies: `quotes`. Transcripts side by side: `episodes`. A tool definition: `code_card`.

## Size

The default size, `screen`, fits posts, Discord and artifacts. For a paper pass `size="paper"` (full text width)
or `size="column"` and save a `.pdf`; for a talk, `size="slide"` gives a 16:9 slide. One size per write-up:
`vl.set_defaults(size="paper")`. Titles must fit on one line at the chosen size.

## Colors

Name the conditions once, at the top of the script, and let vellum color them: coral for the baseline, blue for the
intervention, sage for a second intervention, dark for a reference, and gray for everything else.

```python
vl.set_roles(baseline="Closed book", intervention="With search")
```

Don't hand-pick `colors=` unless a chart needs a color no role gives. One chart can add roles with `roles={...}`,
and JSON specs take a `"roles"` key.

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
bars are ("Error bars are 95% intervals"). The measure and unit go in the axis label, or in the title when the
chart has no axis label. Sample sizes, methods, training details (steps, seeds, layers) and model names go in the
text. If the measure needs a sentence to explain, show a simpler measure.

Labels: two significant digits (41%, not 41.3%), and one name per condition, the same in every figure and in the
text.

Check: read the title alone. Someone outside the project should be able to repeat the finding without asking
what a word means.

## Checks and alt text

- Saving a figure prints `vellum check` warnings for titles, subtitles, decimals and colors that break these rules.
  Fix every one before you send the figure. `vellum check spec.json` checks specs without rendering.
- In a write-up, use `fig.alt_text()` as the image's alt text: it gives the title and the data in words.
  `vellum render --alt` prints it for specs.

## Style rules

- Use `frame="blog"` for write-ups.
- No figure captions at the bottom, in the image or under it in a write-up. What a caption would say goes in
  the text.
- Colors keep their meaning across a write-up: set them with `vl.set_roles` (see Colors) and keep one accent
  per figure.
- Values are percents by default: pass 37 for 37%, and `unit=""` for scores. Show intervals when a claim
  depends on them, and name them in the subtitle.
- Numbers must come from the run files. Label fake or example data as such in the subtitle.
- Look at every PNG before you send it.
