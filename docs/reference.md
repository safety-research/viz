# Reference

Every chart and option, the command line, and how viz works. [The guide](guide.md) covers how to make a good
figure; [the examples](../examples/README.md) are templates to copy.

- [Install](#install)
- [Use it from any project](#use-it-from-any-project)
- [Output](#output)
- [Charts](#charts)
- [Data](#data)
- [Command line](#command-line)
- [How it works](#how-it-works)

## Install

Clone the repo anywhere and run `install.sh`:

```bash
gh repo clone safety-research/viz
viz/install.sh
```

It puts the `viz` command on your PATH (`uv tool install --editable`), links the Claude Code skill in `skill/`
into `~/.claude/skills/viz`, and installs the headless Chromium that renders PNG and PDF. The clone is the
installation: the command and the skill both point back into it, so edits take effect at once and `git pull`
updates everything. `viz path` prints where the clone is. Re-running is safe; `VIZ_NO_TOOL=1` skips the command and
`VIZ_NO_BROWSER=1` the Chromium step.

viz used to be called vellum. `import vellum` and the `vellum` command still work, so older scripts keep running.

## Use it from any project

A one-off script can use it straight from the clone:

```bash
uv run --with-editable "$(viz path)" python make_figs.py
```

Add it to a project:

```bash
uv add --editable "$(viz path)"
```

To make a figure without writing Python, put a JSON spec in a file. Each spec takes the same keys as the chart's
arguments, plus `"chart"`, `"roles"` and `"out"`, and a list of specs makes several figures:

```json
{"chart": "hbar", "data": {"Closed book": 59, "With search": 12},
 "roles": {"baseline": "Closed book", "intervention": "With search"},
 "title": "With search, wrong answers fell from 59% to 12%"}
```

```bash
viz check spec.json && viz render spec.json -o fig.png --alt
```

## Output

Every chart returns a `Figure`. `.save()` picks the format from the extension:

| Extension | What you get |
|---|---|
| `.png` | 2x raster (2016 px wide), rendered by headless Chromium. For web pages, chat and slides. |
| `.pdf` | Vector PDF with the fonts embedded. For papers. |
| `.svg` | One SVG with the used glyphs embedded. It renders the same anywhere and opens in Figma or Illustrator. |
| `.html` | A standalone page. `fig.html(standalone=False)` gives a `<figure>` to paste into a page. |

`fig.svg()` returns the SVG string, `fig.alt_text()` the figure in words, and `fig.check()` the style rules it
breaks. In Jupyter a figure displays itself.

## Charts

Each chart has templates in [examples/](../examples/README.md), grouped the same way.

| Function | Use it for |
|---|---|
| **Compare conditions** | |
| `hbar(data, ...)` | Rates by condition or model. One series or grouped (`series=[...]`), `notes`, `ci`, a `ref` line, `viz.section("heading")` rows, `runs=` dots. |
| `bars(data, ...)` | Vertical bars: the baseline next to the intervention per model, value on top, whiskers, a dashed `ref` line. `runs={label: [v, ...]}` draws each run or seed as a dot over its bar. |
| `dotplot(data, ...)` | Effects with intervals on one axis (a forest plot): a dot per row, `ci`, a `ref` line, `series` offsets, `notes`. |
| `dumbbell(data, ...)` | Before and after per model. |
| **Show change over training** | |
| `line(series, ...)` | Curves over steps or doses, labeled at the end, with `bands`, `xscale="category"` or `"log"`, and `runs=` for each run as a faint line under the mean. |
| **Show a distribution** | |
| `histogram(data, ...)` | One distribution, or up to three overlaid. Freedman-Diaconis bins or `bins=`, `stat="count"` or `"percent"`. |
| `box(data, ...)` | Tukey box plots per group, `points=True` for every value, `horizontal=True`, grouped `series`. |
| `strip(data, ...)` | One dot per item or run in each group, the mean as a line, `ci=True` for 95% intervals. |
| **Show a relationship** | |
| `scatter(points, ...)` | One dot per dataset or model, with labels, `diagonal=`, `trend="fit"` and annotations. |
| `heatmap(data, ...)` | Model by condition tables. One hue (`scale="blue"`, `"coral"`, `"sage"`, `"green"`) or `"diverging"`, plus `col_groups`. |
| **Show where outcomes went** | |
| `stacked(data, series=...)` | Where the outcomes went. |
| **Show what the model did** | |
| `quotes(replies, prompt=...)` | A message and contrasting replies (`viz.Reply`). |
| `episodes([viz.Episode(...)])` | Transcript excerpts side by side: reasoning quote, tool call, outcome dot. |
| `chat(turns, ...)` | A conversation turn by turn: `(role, text)` pairs for user, assistant, system, tool_call and tool_result; `highlight=` turns and `notes={i: "..."}`. |
| `tokens(items, ...)` | Text with each token shaded by a value, such as a probe score: `[(token, value), ...]` or `{row label: [...]}` for several rows; the heatmap's `scale`, `center`, `low`, `high`; a color bar with `label`. |
| **Lay out several figures** | |
| `panels([fig, fig, ...], cols=2)` | Small multiples with one shared legend. Each chart's title becomes its panel title. |

The library also keeps `ecdf`, `violin`, `tiles` (big-number tiles), `waffle` and `code_card` (a tool definition)
for older scripts. They have no template because the charts above cover what research write-ups need.

Every chart takes `title=`, `subtitle=`, `frame=` (`"blog"` for write-ups), `size=` (see
[the guide](guide.md#sizes)), `width=` in px, and `roles=` (see [the guide](guide.md#colors)).

## Data

Data can be `{label: value}`, `{label: [v1, v2]}` (grouped), a list of `(label, value)` pairs, or a pandas
Series or DataFrame. Values are percents by default (`37` means 37%). Pass `unit=""` for scores and means.
`decimals=`, `fmt="{:.1f}%"`, `domain=(lo, hi)` and `ticks=[...]` override the defaults.

The distribution charts take the raw values: `{group: [v, ...]}`, or a plain list for one `histogram` or `ecdf`.
`box`, `strip`, `violin` and `dotplot` keep the percent default; `histogram` and `ecdf` measure plain numbers on x
and show counts or percents of items on y. None and NaN are skipped everywhere.

Colors are names from `viz.PALETTE`, or role names such as `"intervention"`: the control `gray`; the interventions
`coral` (also `orange`), `blue`, `sage`, `plum` (also `purple`) and `ochre`; the muted `gray`, `gray-light` and
`gray-dark`; `beige` for a neutral outcome; and `dark`, `light-blue`, `navy`, `deep-blue`, `olive`, `mid`,
`light-sage`, `deep-sage`, `light-coral` and `clay`. Hex values also work. Run `viz colors` to list them.

## Command line

```
viz render spec.json -o fig.png     one spec or a list of specs (JSON); '-' reads stdin; --alt prints alt text
viz check spec.json                 the style rules each spec breaks (exit 1 if any), without rendering
viz gallery -o out/                 render every template
viz colors                          print the roles and palettes; -o colors.png draws the card
viz roles                           the color roles in effect here and the file they came from
viz path                            this clone's folder
viz setup                           install the headless Chromium that renders PNG and PDF
viz --theme dark ...                any command in the dark theme
```

## How it works

Python builds one SVG per figure. Text is measured with the bundled font files: Newsreader, DM Sans and
JetBrains Mono, all under the OFL, in `src/viz/fonts`. Labels, wrapping and margins are computed before anything
is drawn. One headless Chromium, started on first use and reused, turns the SVG into PNG or PDF in about 0.1 s
per figure. Run the tests with `uv run pytest`.
