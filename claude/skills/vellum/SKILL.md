---
name: vellum
description: "vellum house figure style: cream paper, Newsreader serif claim titles, DM Sans labels, coral = baseline / blue = intervention, direct value labels. The ~/dev/vellum library makes it in one call (hbar, bars, heatmap, tiles, waffle, scatter, dumbbell, line, stacked, panels, quote/transcript/tool cards) and saves PNG (2x), PDF, SVG or HTML. Use this whenever you make any chart, plot, graph or figure: results for Discord, write-ups, blog drafts, artifacts, papers, slides, 'dream figures' with fake data, or 'figures in our style'. Prefer it over other figure skills and plain matplotlib unless the user asks for those."
---

# vellum: house figure style

The library is at `~/dev/vellum`. The README there has the full API, and `docs/gallery/*.png` shows every chart
type. The source of every gallery figure is in `src/vellum/gallery.py`, so copy the closest one.

## Run it

You don't need to install anything:

```bash
uv run --with-editable ~/dev/vellum python make_figs.py
```

To render a JSON spec (one dict, or a list with an "out" path on each):

```bash
uvx --from ~/dev/vellum vellum render spec.json -o fig.png
```

```python
import vellum as vl
fig = vl.hbar({"Closed book": 59, "With search": 12}, colors={"Closed book": "coral"}, highlight="With search",
              title="Search cut wrong answers fivefold",                         # the claim, as a sentence
              subtitle="Share of 400 questions answered wrong, closed book and with search")  # measure, sample
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

## Style rules

- Titles are plain, easy to read, and state a result: one short sentence in everyday words that says what
  happened ("Search cut wrong answers fivefold"), not what the chart covers ("Wrong answers by setup"). Leave
  out jargon, abbreviations and tool or variable names. The subtitle gives the measure, unit and sample.
  Use `frame="blog"` for write-ups.
- No figure captions at the bottom, in the image or under it in a write-up. What a caption would say, such as
  the sample or which intervals are shown, goes in the subtitle.
- Colors keep their meaning. Coral is the baseline or bad outcome, blue the intervention or the point, sage a
  second intervention (fine-tuning, a different prompt), beige untouched, and gray the rest. Use one accent per
  figure.
- Values are percents by default: pass 37 for 37%, and `unit=""` for scores. Show intervals when a claim
  depends on them, and name them in the subtitle.
- Numbers must come from the run files. Label fake or example data as such in the title or subtitle.
- Look at every PNG before you send it.
