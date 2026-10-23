# viz examples

Every figure here is a template: find the question your figure answers, copy its code and change the
numbers. Every number is made up, and error bars and bands are 95% intervals. Run one with
`uv run --with-editable "$(viz path)" python ex.py`. This page is generated from `src/viz/gallery.py`
(`viz gallery --examples examples/README.md`), so edit that file, not this one.

<table>
<tr><td colspan="3"><b><a href="#compare-conditions">Compare conditions</a></b> · One number per condition, or per model and condition, with its interval.</td></tr>
<tr><td width="33%" valign="top"><a href="#rates-by-condition-the-baseline-and-the-intervention-named-by-role"><img src="../docs/gallery/01_hbar.png" alt="Rates by condition, the baseline and the intervention named by role"></a><br>Rates by condition, the baseline and the intervention named by role</td><td width="33%" valign="top"><a href="#each-model-with-and-without-the-intervention"><img src="../docs/gallery/02_bars.png" alt="Each model with and without the intervention"></a><br>Each model with and without the intervention</td><td width="33%" valign="top"><a href="#the-mean-over-runs-with-every-run-as-a-dot"><img src="../docs/gallery/03_bars_runs.png" alt="The mean over runs, with every run as a dot"></a><br>The mean over runs, with every run as a dot</td></tr>
<tr><td width="33%" valign="top"><a href="#an-effect-and-its-interval-for-each-model-against-zero"><img src="../docs/gallery/04_dotplot.png" alt="An effect and its interval for each model, against zero"></a><br>An effect and its interval for each model, against zero</td><td width="33%" valign="top"><a href="#before-and-after-for-each-model"><img src="../docs/gallery/05_dumbbell.png" alt="Before and after for each model"></a><br>Before and after for each model</td></tr>
<tr><td colspan="3"><b><a href="#show-change-over-training">Show change over training</a></b> · A measure over training steps, doses or compute.</td></tr>
<tr><td width="33%" valign="top"><a href="#a-training-curve-with-every-run-faint-behind-the-mean"><img src="../docs/gallery/06_line_runs.png" alt="A training curve, with every run faint behind the mean"></a><br>A training curve, with every run faint behind the mean</td></tr>
<tr><td colspan="3"><b><a href="#show-a-distribution">Show a distribution</a></b> · Many values per condition, such as answer lengths, times or scores per item.</td></tr>
<tr><td width="33%" valign="top"><a href="#two-distributions-overlaid"><img src="../docs/gallery/07_histogram.png" alt="Two distributions overlaid"></a><br>Two distributions overlaid</td><td width="33%" valign="top"><a href="#distributions-per-condition-for-many-items-each"><img src="../docs/gallery/08_box.png" alt="Distributions per condition, for many items each"></a><br>Distributions per condition, for many items each</td><td width="33%" valign="top"><a href="#one-dot-per-item-with-the-mean-and-its-interval"><img src="../docs/gallery/09_strip.png" alt="One dot per item, with the mean and its interval"></a><br>One dot per item, with the mean and its interval</td></tr>
<tr><td colspan="3"><b><a href="#show-a-relationship">Show a relationship</a></b> · Two measures against each other, or models against conditions.</td></tr>
<tr><td width="33%" valign="top"><a href="#one-dot-per-dataset-against-a-reference-line"><img src="../docs/gallery/10_scatter.png" alt="One dot per dataset, against a reference line"></a><br>One dot per dataset, against a reference line</td><td width="33%" valign="top"><a href="#models-by-conditions"><img src="../docs/gallery/11_heatmap.png" alt="Models by conditions"></a><br>Models by conditions</td></tr>
<tr><td colspan="3"><b><a href="#show-where-outcomes-went">Show where outcomes went</a></b> · Shares that add up to 100%.</td></tr>
<tr><td width="33%" valign="top"><a href="#where-the-outcomes-went-coral-is-the-bad-outcome"><img src="../docs/gallery/12_stacked.png" alt="Where the outcomes went (coral is the bad outcome)"></a><br>Where the outcomes went (coral is the bad outcome)</td></tr>
<tr><td colspan="3"><b><a href="#show-what-the-model-did">Show what the model did</a></b> · Replies and transcripts, as text.</td></tr>
<tr><td width="33%" valign="top"><a href="#one-prompt-and-contrasting-replies"><img src="../docs/gallery/13_quotes.png" alt="One prompt and contrasting replies"></a><br>One prompt and contrasting replies</td><td width="33%" valign="top"><a href="#what-the-model-did-transcripts-side-by-side"><img src="../docs/gallery/14_episodes.png" alt="What the model did, transcripts side by side"></a><br>What the model did, transcripts side by side</td></tr>
<tr><td colspan="3"><b><a href="#lay-out-several-figures">Lay out several figures</a></b> · Panels that share one legend, for a paper figure or a slide.</td></tr>
<tr><td width="33%" valign="top"><a href="#several-comparisons-that-share-one-legend"><img src="../docs/gallery/15_panels.png" alt="Several comparisons that share one legend"></a><br>Several comparisons that share one legend</td></tr>
</table>

## Compare conditions

One number per condition, or per model and condition, with its interval.

### Rates by condition, the baseline and the intervention named by role

![hbar](../docs/gallery/01_hbar.png)

```python
import viz

viz.hbar(
    {"Closed book": 41.0, "Search snippets": 63.5, "Full documents": 88.0}, highlight="Full documents", decimals=0,
    roles={"baseline": "Closed book", "intervention": "Full documents"},
    notes={"Closed book": "164 of 400", "Search snippets": "254 of 400", "Full documents": "352 of 400"},
    title="Full documents raised correct answers from 41% to 88%").save("hbar.png")
```

### Each model with and without the intervention

![bars](../docs/gallery/02_bars.png)

```python
import viz
from viz.gallery import WRONG_BY_MODEL

viz.bars(
    WRONG_BY_MODEL, series=["Closed book", "With search"], decimals=0, ylabel="Questions answered wrong", frame="blog",
    roles={"baseline": "Closed book", "intervention": "With search"},
    title="Search cut wrong answers for all ten models").save("bars.png")
```

### The mean over runs, with every run as a dot

![bars_runs](../docs/gallery/03_bars_runs.png)

```python
import viz
from viz.gallery import WRONG_BY_SEED

viz.bars(
    {arm: sum(runs) / len(runs) for arm, runs in WRONG_BY_SEED.items()}, runs=WRONG_BY_SEED,
    roles={"baseline": "Plain fine-tune", "intervention": "Worked examples"}, ref=31, ref_label="Base model",
    decimals=0, ylabel="Questions answered wrong",
    title="Worked examples cut wrong answers from 34% to 19% in every run").save("bars_runs.png")
```

### An effect and its interval for each model, against zero

![dotplot](../docs/gallery/04_dotplot.png)

```python
import viz
from viz.gallery import WRONG_BY_MODEL, diff_ci

viz.dotplot(
    {m: b - a for m, (a, b) in WRONG_BY_MODEL.items()},
    ci={m: diff_ci(a, b, 200) for m, (a, b) in WRONG_BY_MODEL.items()}, ref=0, unit="", decimals=0,
    xlabel="Change in wrong answers with search (percentage points)",
    title="Search cut each model's wrong answers by 8 to 46 points").save("dotplot.png")
```

### Before and after for each model

![dumbbell](../docs/gallery/05_dumbbell.png)

```python
import viz
from viz.gallery import RATINGS

viz.dumbbell(
    RATINGS, series=("Closed book", "With search"), unit="", decimals=1, ticks=[1, 2, 3, 4, 5, 6, 7],
    roles={"baseline": "Closed book", "intervention": "With search"},
    missing="not rated", title="Every rated model got higher helpfulness ratings with search").save("dumbbell.png")
```

## Show change over training

A measure over training steps, doses or compute.

### A training curve, with every run faint behind the mean

![line_runs](../docs/gallery/06_line_runs.png)

```python
import viz
from viz.gallery import STEPS, WRONG_DURING_TRAINING, mean_curve

viz.line(
    {arm: mean_curve(runs) for arm, runs in WRONG_DURING_TRAINING.items()}, x=STEPS, runs=WRONG_DURING_TRAINING,
    roles={"baseline": "Plain fine-tune", "intervention": "Worked examples"}, markers=False, decimals=0,
    xlabel="Training step", title="Worked examples cut wrong answers from 31% to 18% during training").save("line_runs.png")
```

## Show a distribution

Many values per condition, such as answer lengths, times or scores per item.

### Two distributions overlaid

![histogram](../docs/gallery/07_histogram.png)

```python
import viz
from viz.gallery import ANSWER_WORDS

viz.histogram(
    ANSWER_WORDS, stat="percent", roles={"baseline": "Closed book", "intervention": "With search"}, xlabel="Answer length (words)", ylabel="Share of answers",
    title="With search, the median answer grew from 84 to 150 words").save("histogram.png")
```

### Distributions per condition, for many items each

![box](../docs/gallery/08_box.png)

```python
import viz
from viz.gallery import SECONDS

viz.box(
    SECONDS, roles={"baseline": "Closed book", "intervention": "Full documents"}, unit="", decimals=1,
    ylabel="Seconds to answer", title="Full documents raised the median answer time from 2.9 to 9.2 seconds").save("box.png")
```

### One dot per item, with the mean and its interval

![strip](../docs/gallery/09_strip.png)

```python
import viz
from viz.gallery import WRONG_BY_TOPIC, WRONG_WITH_SEARCH_BY_TOPIC

viz.strip(
    {"Closed book": list(WRONG_BY_TOPIC.values()), "With search": list(WRONG_WITH_SEARCH_BY_TOPIC.values())},
    ci=True, roles={"baseline": "Closed book", "intervention": "With search"}, decimals=0, ylabel="Wrong answers per topic",
    title="Search cut wrong answers from 28% to 8% for the average topic").save("strip.png")
```

## Show a relationship

Two measures against each other, or models against conditions.

### One dot per dataset, against a reference line

![scatter](../docs/gallery/10_scatter.png)

```python
import viz
from viz.gallery import SEARCHES

viz.scatter(
    SEARCHES, xunit="%", xticks=[0, 10, 20, 30, 40, 50, 60, 70], yticks=[0, 10, 20, 30, 40, 50, 60, 70, 80],
    labels=["Tech News", "Election Facts", "Health FAQ", "Sports Desk", "Recipe Box"],
    diagonal="one search per question that needs one",
    annotations=[(2, 76, "Above the line: more searches than\nquestions that needed them")],
    xlabel="Share of questions that need recent facts", ylabel="Searches per 100 questions",
    title="Datasets with more questions about recent events drew more searches").save("scatter.png")
```

### Models by conditions

![heatmap](../docs/gallery/11_heatmap.png)

```python
import viz
from viz.gallery import FINISHED

viz.heatmap(
    FINISHED, cols=["Small", "Medium", "Large", "Huge"], col_groups=[("Long tasks", ["Large", "Huge"])],
    title="Three of eight models finished most of the huge tasks").save("heatmap.png")
```

## Show where outcomes went

Shares that add up to 100%.

### Where the outcomes went (coral is the bad outcome)

![stacked](../docs/gallery/12_stacked.png)

```python
import viz

viz.stacked(
    {"Closed book": [41, 0, 59], "With search": [76, 12, 12]}, series=["Right", "Said it didn’t know", "Wrong"],
    colors=["blue", "beige", "coral"],
    title="With search, wrong answers fell from 59% to 12%").save("stacked.png")
```

## Show what the model did

Replies and transcripts, as text.

### One prompt and contrasting replies

![quotes](../docs/gallery/13_quotes.png)

```python
import viz

viz.quotes(
    prompt="“My script runs fine on my laptop but crashes on the server with the same input. What should I check?”",
    replies=[viz.Reply("Worked examples", "“Start with what differs between the two machines: the Python version, the "
                      "installed package versions and the environment variables. Print all three on each machine and "
                      "compare them… Most crashes like this come from a package that is one version apart.”",
                      "trained on step-by-step answers", "intervention"),
             viz.Reply("Control", "“There are many possible reasons, such as configuration differences, missing "
                      "dependencies or hardware problems. Check the server logs for error messages… You could also "
                      "try reinstalling your dependencies.”", "plain fine-tune", "control")],
    title="The trained model narrowed the problem down instead of listing causes").save("quotes.png")
```

### What the model did, transcripts side by side

![episodes](../docs/gallery/14_episodes.png)

```python
import viz

viz.episodes([
    viz.Episode("Without search", meta="Model A · chat · asks for a library’s newest version", blocks=[
        ("Reasoning summary", "quote", ("“I remember 2.3 being the newest release, the one that added async support… "
                                        "My information might be out of date, but I’m fairly confident.”")),
        ("Answer", "code", "“The newest version is 2.3. Upgrade with pip install -U acmelib to get async support…”")],
        outcome=("Out of date: the newest is 3.0", "coral")),
    viz.Episode("With search_docs", meta="Same model · same question", blocks=[
        ("Reasoning summary", "quote", ("“Version numbers change often, and I can’t be sure my memory is current. "
                                        "I should check the release notes.”")),
        ("search_docs", "code", "“query: acmelib release notes, newest version”")],
        outcome=("Answered 3.0, with a link", "blue"))],
    frame="blog", title="With search, the model checked the release notes instead of guessing").save("episodes.png")
```

## Lay out several figures

Panels that share one legend, for a paper figure or a slide.

### Several comparisons that share one legend

![panels](../docs/gallery/15_panels.png)

```python
import viz
from viz.gallery import wilson_cis

small = {"unit": "%", "decimals": 0, "ylabel": "Wrong answers", "ticks": [0, 10, 20, 30, 40, 50]}
prompts = {"Closed book": 38.5, "Longer prompt": 36.0, "Careful prompt": 35.2, "Search": 9.5}
bigger = {"Small model": 38.5, "Twice the size": 27.0, "Small with search": 9.5, "Both": 7.8}
index = {"Closed book": 38.5, "Year-old index": 24.0, "Month-old": 13.1, "Week-old": 10.2, "Live index": 9.5}
empty = {"Closed book": 38.5, "Search answered": 9.5, "Search found nothing": 31.0}
viz.panels([
    viz.bars(prompts, ci=wilson_cis(prompts, 1200),
            title="(a) Better prompts", **small),
    viz.bars(bigger, ci=wilson_cis(bigger, 1200),
            title="(b) A bigger model", **small),
    viz.bars(index, ci=wilson_cis(index, 1200),
            title="(c) Search index age", **small),
    viz.bars(empty, ci=wilson_cis(empty, 1200), sort=False,
            title="(d) When search finds nothing", **small)],
    legend={"Closed book": "control", "Other fixes": "gray", "Search": "intervention", "Search that finds nothing": "second"},
    roles={"baseline": ["Closed book", "Small model"],
           "intervention": ["Search", "Small with search", "Both", "Search answered"],
           "second": "Search found nothing", "ordered": ["Year-old index", "Month-old", "Week-old", "Live index"]},
    frame="blog", title="Search cut wrong answers more than better prompts or a bigger model").save("panels.png")
```

## No Python: a JSON spec

A list of specs makes several figures; each takes the same keys as the
chart's arguments, plus `"chart"`, `"roles"` and `"out"`.

```json
{"chart": "hbar", "data": {"Closed book": 59, "With search": 12},
 "roles": {"baseline": "Closed book", "intervention": "With search"},
 "title": "With search, wrong answers fell from 59% to 12%"}
```

```bash
viz check fivefold.json && viz render fivefold.json -o fivefold.png --alt
```
