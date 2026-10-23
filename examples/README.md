# vellum examples

One snippet per chart type. Each makes the figure named in its `.save()` call, and every number is made up.
Run one with `uv run --with-editable "$(vellum path)" python ex.py`.

## 1. Horizontal bars: one accent on the point, notes after the value

```python
import vellum as vl

vl.hbar({"Closed book": 41.0, "Search snippets": 63.5, "Full documents": 88.0},
        highlight="Full documents", decimals=0,
        notes={"Closed book": "164 of 400", "Search snippets": "254 of 400", "Full documents": "352 of 400"},
        title="Full documents raised correct answers from 41% to 88%",
        ).save("hbar_highlight.png")
```

## 2. Row groups and a reference line (`vl.section`, `ref=`)

```python
import vellum as vl

vl.hbar([("Base model", 31.0), ("Plain fine-tune (control)", 33.5), ("Worked examples", 18.2),
         vl.section("Other data"), ("Textbook passages", 27.4), ("Forum answers", 36.9), ("Short answers only", 22.6)],
        roles={"reference": "Base model", "intervention": "Worked examples"}, highlight="Worked examples",
        ref=31.0, decimals=0,
        notes={"Forum answers": "worse than the base model"},
        title="Worked examples cut wrong answers from 31% to 18%",
        ).save("hbar_sections.png")
```

## 3. Panels with a shared legend (grouped bars, a 1 to 7 scale next to a percent)

```python
import vellum as vl

series = ["Closed book", "With search"]
vl.panels([
    vl.hbar({"Recent events": [3.10, 5.45], "Settled facts": [5.60, 5.72]}, series=series,
            unit="", decimals=1, ticks=[1, 2, 3, 4, 5, 6, 7], title="Helpfulness, 1 to 7"),
    vl.hbar({"Recent events": [31.5, 74.0], "Settled facts": [80.5, 82.0]}, series=series,
            decimals=0, title="Would ask it again")],
    title="With search, people rated answers on recent events higher",
    ).save("panels_grouped.png")
```

## 4. Vertical bars in the blog frame (centered title, legend below)

```python
import vellum as vl
from vellum.gallery import WRONG_BY_MODEL  # {"Model A": [12.5, 4.0], ...}: closed book, with search

vl.bars(WRONG_BY_MODEL, series=["Closed book", "With search"], decimals=0, ylabel="Questions answered wrong",
        frame="blog", title="Search cut wrong answers for all ten models",
        ).save("bars_blog.png")
```

## 5. Small multiples with intervals (`ci=` whiskers, one legend for all panels)

```python
import vellum as vl

kw = dict(ylabel="Wrong answers", decimals=0, ticks=[0, 10, 20, 30, 40, 50])
vl.panels([
    vl.bars({"Small model": 38.5, "Twice the size": 27.0, "Small with search": 9.5, "Both": 7.8},
            ci={"Small model": (35.8, 41.3), "Twice the size": (24.6, 29.6), "Small with search": (8.0, 11.3),
                "Both": (6.4, 9.5)},
            title="(a) A bigger model", **kw),
    vl.bars({"Closed book": 38.5, "Search answered": 9.5, "Search found nothing": 31.0},
            ci={"Closed book": (35.8, 41.3), "Search answered": (8.0, 11.3), "Search found nothing": (28.4, 33.7)},
            title="(b) When search finds nothing", **kw)],
    roles={"baseline": ["Small model", "Closed book"], "intervention": ["Small with search", "Both", "Search answered"],
           "second": "Search found nothing"},
    legend={"Closed book": "dark", "A bigger model": "gray", "Search": "blue", "Search that finds nothing": "plum"},
    frame="blog", title="Search cut wrong answers more than a model twice the size",
    ).save("small_multiples.png")
```

## 6. Heatmap table (one hue, more is darker, grouped column heading)

```python
import vellum as vl
from vellum.gallery import FINISHED  # {"Model A": [100, 100, 100, 96.7], ..., "Model H": [93.3, 70.0, 6.7, 0]}

vl.heatmap(FINISHED, cols=["Small", "Medium", "Large", "Huge"], col_groups=[("Long tasks", ["Large", "Huge"])],
           title="Three of eight models finished most of the huge tasks",
           ).save("heatmap.png")
```

## 7. Number tiles (a confusion matrix; `strong=True` fills the tile that makes the point)

```python
import vellum as vl
T = vl.Tile

vl.tiles([[T(412, ["agreed the answer was right", "94% of the answers people accepted"], "blue", strong=True),
           T(38, ["accepted a wrong answer", "the costly mistake"], "coral")],
          [T(27, ["rejected a right answer", "mostly unusual formats"], "beige"),
           T(523, ["agreed the answer was wrong"], "gray")]],
         col_headers=[("People said right", "439 answers"), ("People said wrong", "561 answers")],
         row_headers=[("Grader said right", "450 answers"), ("Grader said wrong", "550 answers")],
         title="The automatic grader agreed with people on 935 of 1,000 answers",
         ).save("tiles.png")
```

## 8. Scatter (labels placed automatically, a y = x line with its own label)

```python
import vellum as vl
from vellum.gallery import SEARCHES  # {dataset: (% of questions needing recent facts, searches per 100 questions)}

vl.scatter(SEARCHES, xunit="%", diagonal="one search per question that needs one",
           labels=["Tech News", "Election Facts", "Health FAQ", "Sports Desk"],
           xlabel="Share of questions that need recent facts", ylabel="Searches per 100 questions",
           title="Datasets with more questions about recent events drew more searches",
           ).save("scatter.png")
```

## 9. Dumbbell and waffle

```python
import vellum as vl
from vellum.gallery import RATINGS  # {"Model A": (5.1, 6.2), "Model C": (None, None), ...}

vl.dumbbell(RATINGS, series=("Closed book", "With search"), unit="", decimals=1, ticks=[1, 2, 3, 4, 5, 6, 7],
            missing="not rated", title="Every rated model got higher helpfulness ratings with search",
            ).save("dumbbell.png")
```
```python
vl.waffle({"Out-of-date fact": 210, "Misread the question": 140, "Arithmetic slip": 90, "Grader error": 60},
          count_label="answers", title="Out-of-date facts caused 42 in 100 wrong answers",
          ).save("waffle.png")
```

## 10. Line and stacked bars

```python
import vellum as vl

vl.line({"Worked examples": [31, 26, 21, 17], "Plain fine-tune": [31, 32, 33, 34]}, x=[0, 1, 3, 10],
        xscale="category", xtick_labels={0: "0", 1: "1M", 3: "3M", 10: "10M"},
        roles={"baseline": "Plain fine-tune", "intervention": "Worked examples"},
        bands={"Worked examples": ([27, 22, 17, 13], [35, 30, 25, 21])}, xlabel="Fine-tuning tokens",
        title="Wrong answers fell from 31% to 17% with more worked examples",
        ).save("line.png")
```
```python
vl.stacked({"Closed book": [41, 0, 59], "With search": [76, 12, 12]},
           series=["Right", "Said it didn’t know", "Wrong"], colors=["blue", "beige", "coral"],
           title="With search, wrong answers fell from 59% to 12%",
           ).save("stacked.png")
```

## 11. Text figures: quoted replies and a tool definition

```python
import vellum as vl
from vellum.gallery import TOOL  # a made-up tool description

vl.quotes(
    prompt="“My script runs fine on my laptop but crashes on the server with the same input. What should I check?”",
    replies=[vl.Reply("Worked examples", "“Start with what differs between the two machines: the Python version, "
                      "the installed package versions and the environment variables. …”",
                      "trained on step-by-step answers", "blue"),
             vl.Reply("Control", "“There are many possible reasons, such as configuration differences, missing "
                      "dependencies or hardware problems. Check the server logs for error messages. …”",
                      "plain fine-tune", "gray")],
    title="The trained model narrowed the problem down instead of listing causes",
).save("quotes.png")

vl.code_card("search_docs", {"query": "What to look up, in a few words."}, TOOL).save("tool.png")
```

## 12. Transcript excerpts side by side (`vl.episodes`)

```python
import vellum as vl

vl.episodes([
    vl.Episode("Without search", meta="Model A · chat", outcome=("Out of date: the newest is 3.0", "coral"), blocks=[
        ("Reasoning summary", "quote", "“I remember 2.3 being the newest release… but I’m fairly confident.”"),
        ("Answer", "code", "“The newest version is 2.3. Upgrade with pip install -U acmelib…”")]),
    vl.Episode("With search_docs", meta="Same model · same question", outcome=("Answered 3.0, with a link", "blue"),
               blocks=[("Reasoning summary", "quote", "“Version numbers change often… I should check the release notes.”"),
                       ("search_docs", "code", "“query: acmelib release notes, newest version”")])],
    frame="blog", title="With search, the model checked the release notes instead of guessing",
).save("episodes.png")
```

## 13. No Python: a JSON spec through the CLI (a list of specs makes several figures)

```json
{
 "chart": "hbar",
 "data": {
  "Closed book": 59,
  "With search": 12
 },
 "colors": {
  "Closed book": "coral"
 },
 "highlight": "With search",
 "title": "With search, wrong answers fell from 59% to 12%"
}
```
```bash
vellum render fivefold.json -o fivefold.png
```
