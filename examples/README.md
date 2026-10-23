# viz examples

Every gallery figure with the code that makes it. Every number is made up, and error bars and bands are 95%
intervals. Run one with `uv run --with-editable "$(viz path)" python ex.py`. This page is generated from
`src/viz/gallery.py` (`viz gallery --examples examples/README.md`), so edit that file, not this one.

## 1. Rates by condition, the baseline and the intervention named by role

![hbar](../docs/gallery/01_hbar.png)

```python
import viz

viz.hbar(
    {"Closed book": 41.0, "Search snippets": 63.5, "Full documents": 88.0}, highlight="Full documents", decimals=0,
    roles={"baseline": "Closed book", "intervention": "Full documents"},
    notes={"Closed book": "164 of 400", "Search snippets": "254 of 400", "Full documents": "352 of 400"},
    title="Full documents raised correct answers from 41% to 88%").save("01_hbar.png")
```

## 2. Each model with and without the intervention

![bars](../docs/gallery/02_bars.png)

```python
import viz
from viz.gallery import WRONG_BY_MODEL

viz.bars(
    WRONG_BY_MODEL, series=["Closed book", "With search"], decimals=0, ylabel="Questions answered wrong", frame="blog",
    roles={"baseline": "Closed book", "intervention": "With search"},
    title="Search cut wrong answers for all ten models").save("02_bars.png")
```

## 3. The mean over runs, with every run as a dot

![bars_runs](../docs/gallery/03_bars_runs.png)

```python
import viz
from viz.gallery import WRONG_BY_SEED

viz.bars(
    {arm: sum(runs) / len(runs) for arm, runs in WRONG_BY_SEED.items()}, runs=WRONG_BY_SEED,
    roles={"baseline": "Plain fine-tune", "intervention": "Worked examples"}, ref=31, ref_label="Base model",
    decimals=0, ylabel="Questions answered wrong",
    title="Worked examples cut wrong answers from 34% to 19% in every run").save("03_bars_runs.png")
```

## 4. An effect and its interval for each model, against zero

![dotplot](../docs/gallery/04_dotplot.png)

```python
import viz
from viz.gallery import WRONG_BY_MODEL, diff_ci

viz.dotplot(
    {m: b - a for m, (a, b) in WRONG_BY_MODEL.items()},
    ci={m: diff_ci(a, b, 200) for m, (a, b) in WRONG_BY_MODEL.items()}, ref=0, unit="", decimals=0,
    xlabel="Change in wrong answers with search (percentage points)",
    title="Search cut each model's wrong answers by 8 to 46 points").save("04_dotplot.png")
```

## 5. A training curve, with every run faint behind the mean

![line_runs](../docs/gallery/05_line_runs.png)

```python
import viz
from viz.gallery import STEPS, WRONG_DURING_TRAINING, mean_curve

viz.line(
    {arm: mean_curve(runs) for arm, runs in WRONG_DURING_TRAINING.items()}, x=STEPS, runs=WRONG_DURING_TRAINING,
    roles={"baseline": "Plain fine-tune", "intervention": "Worked examples"}, markers=False, decimals=0,
    xlabel="Training step", title="Worked examples cut wrong answers from 31% to 18% during training").save("05_line_runs.png")
```

## 6. Several comparisons that share one legend

![panels](../docs/gallery/06_panels.png)

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
    frame="blog", title="Search cut wrong answers more than better prompts or a bigger model").save("06_panels.png")
```

## 7. Models by conditions

![heatmap](../docs/gallery/07_heatmap.png)

```python
import viz
from viz.gallery import FINISHED

viz.heatmap(
    FINISHED, cols=["Small", "Medium", "Large", "Huge"], col_groups=[("Long tasks", ["Large", "Huge"])],
    title="Three of eight models finished most of the huge tasks").save("07_heatmap.png")
```

## 8. One dot per dataset, against a reference line

![scatter](../docs/gallery/08_scatter.png)

```python
import viz
from viz.gallery import SEARCHES

viz.scatter(
    SEARCHES, xunit="%", xticks=[0, 10, 20, 30, 40, 50, 60, 70], yticks=[0, 10, 20, 30, 40, 50, 60, 70, 80],
    labels=["Tech News", "Election Facts", "Health FAQ", "Sports Desk", "Recipe Box"],
    diagonal="one search per question that needs one",
    annotations=[(2, 76, "Above the line: more searches than\nquestions that needed them")],
    xlabel="Share of questions that need recent facts", ylabel="Searches per 100 questions",
    title="Datasets with more questions about recent events drew more searches").save("08_scatter.png")
```

## 9. Before and after for each model

![dumbbell](../docs/gallery/09_dumbbell.png)

```python
import viz
from viz.gallery import RATINGS

viz.dumbbell(
    RATINGS, series=("Closed book", "With search"), unit="", decimals=1, ticks=[1, 2, 3, 4, 5, 6, 7],
    roles={"baseline": "Closed book", "intervention": "With search"},
    missing="not rated", title="Every rated model got higher helpfulness ratings with search").save("09_dumbbell.png")
```

## 10. Where the outcomes went (coral is the bad outcome)

![stacked](../docs/gallery/10_stacked.png)

```python
import viz

viz.stacked(
    {"Closed book": [41, 0, 59], "With search": [76, 12, 12]}, series=["Right", "Said it didn’t know", "Wrong"],
    colors=["blue", "beige", "coral"],
    title="With search, wrong answers fell from 59% to 12%").save("10_stacked.png")
```

## 11. Two distributions overlaid

![histogram](../docs/gallery/11_histogram.png)

```python
import viz
from viz.gallery import ANSWER_WORDS

viz.histogram(
    ANSWER_WORDS, stat="percent", roles={"baseline": "Closed book", "intervention": "With search"}, xlabel="Answer length (words)", ylabel="Share of answers",
    title="With search, the median answer grew from 84 to 150 words").save("11_histogram.png")
```

## 12. Distributions per condition, for many items each

![box](../docs/gallery/12_box.png)

```python
import viz
from viz.gallery import SECONDS

viz.box(
    SECONDS, roles={"baseline": "Closed book", "intervention": "Full documents"}, unit="", decimals=1,
    ylabel="Seconds to answer", title="Full documents raised the median answer time from 2.9 to 9.2 seconds").save("12_box.png")
```

## 13. One dot per item, with the mean and its interval

![strip](../docs/gallery/13_strip.png)

```python
import viz
from viz.gallery import WRONG_BY_TOPIC, WRONG_WITH_SEARCH_BY_TOPIC

viz.strip(
    {"Closed book": list(WRONG_BY_TOPIC.values()), "With search": list(WRONG_WITH_SEARCH_BY_TOPIC.values())},
    ci=True, roles={"baseline": "Closed book", "intervention": "With search"}, decimals=0, ylabel="Wrong answers per topic",
    title="Search cut wrong answers from 28% to 8% for the average topic").save("13_strip.png")
```

## 14. One prompt and contrasting replies

![quotes](../docs/gallery/14_quotes.png)

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
    title="The trained model narrowed the problem down instead of listing causes").save("14_quotes.png")
```

## 15. What the model did, transcripts side by side

![episodes](../docs/gallery/15_episodes.png)

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
    frame="blog", title="With search, the model checked the release notes instead of guessing").save("15_episodes.png")
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
