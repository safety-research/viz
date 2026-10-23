"""Example gallery: one figure per chart type, with made-up numbers and no subtitles.

    viz gallery -o out/      or      python -m viz.gallery out/
"""
from __future__ import annotations

import math
import random
import re
import sys
from pathlib import Path
from statistics import NormalDist

import viz


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return 100 * (c - h), 100 * (c + h)


def wilson_cis(rates: dict[str, float], n: int) -> dict[str, tuple[float, float]]:
    """Wilson intervals for percents that were each measured on n items."""
    return {k: wilson(round(v * n / 100), n) for k, v in rates.items()}


def diff_ci(a: float, b: float, n: int, z: float = 1.96) -> tuple[float, float]:
    """Interval for the difference b - a of two percents, each measured on n items."""
    se = 100 * math.sqrt(a / 100 * (1 - a / 100) / n + b / 100 * (1 - b / 100) / n)
    return b - a - z * se, b - a + z * se


def lognormal(n: int, median: float, spread: float, seed: int, digits: int = 0) -> list[float]:
    """n made-up values with a long right tail, the same on every run and Python version."""
    rng = random.Random(seed)
    dist = NormalDist(math.log(median), spread)
    return [round(math.exp(dist.inv_cdf(rng.random() or 0.5)), digits) for _ in range(n)]




def mean_curve(runs: list[list[float]]) -> list[float]:
    return [sum(step) / len(step) for step in zip(*runs)]


# A made-up study of an assistant that answers questions closed book or with a document search tool.
WRONG_BY_TOPIC = {  # share of 200 questions per topic answered wrong, closed book
    "Software versions": 51, "Exchange rates": 47, "Product prices": 44, "Sports results": 38, "Company leaders": 33,
    "World records": 31, "Election results": 29, "Movie casts": 18, "Chemistry": 12, "Recipes": 11, "Geography": 9,
    "Classic novels": 7,
}
SEARCHES = {  # (share of questions that need recent facts, searches per 100 questions), by dataset
    "History Quiz": (3, 6), "Recipe Box": (5, 4), "Kids Questions": (6, 9), "Science Facts": (8, 14),
    "Law Basics": (12, 22), "Health FAQ": (14, 31), "Trivia Night": (17, 20), "City Guides": (21, 26),
    "Movie Buff": (24, 33), "Travel Tips": (27, 41), "Product Help": (31, 52), "Music Charts": (35, 29),
    "Sports Desk": (42, 37), "Election Facts": (46, 71), "Finance Q&A": (53, 64), "Tech News": (61, 78),
}
FINISHED = {  # share of 30 runs finished within the time limit: small, medium, large and huge tasks
    "Model A": [100, 100, 100, 96.7], "Model B": [100, 100, 96.7, 90.0], "Model C": [100, 100, 93.3, 63.3],
    "Model D": [100, 96.7, 80.0, 40.0], "Model E": [100, 96.7, 56.7, 16.7], "Model F": [100, 90.0, 33.3, 3.3],
    "Model G": [96.7, 83.3, 20.0, 0], "Model H": [93.3, 70.0, 6.7, 0],
}
WRONG_BY_MODEL = {  # share of 200 questions answered wrong: closed book, with search
    "Model A": [12.5, 4.0], "Model B": [18.0, 5.5], "Model C": [22.5, 6.0], "Model D": [27.0, 8.5],
    "Model E": [31.5, 7.0], "Model F": [35.0, 9.5], "Model G": [41.5, 11.0], "Model H": [46.0, 10.5],
    "Model I": [52.5, 14.0], "Model J": [58.0, 12.5],
}
RATINGS = {  # mean helpfulness, 1 (not at all) to 7 (very): closed book, with search; None = not rated
    "Model A": (5.1, 6.2), "Model B": (4.6, 6.0), "Model C": (None, None), "Model D": (4.2, 5.9),
    "Model E": (3.9, 5.7), "Model F": (None, None), "Model G": (3.4, 5.5), "Model H": (3.0, 5.6),
    "Model I": (2.7, 5.2), "Model J": (2.5, 5.0),
}
WRONG_BY_SEED = {  # share of 400 questions answered wrong after fine-tuning, one value per training run (seed)
    "Plain fine-tune": [33.0, 35.5, 31.0, 36.0, 34.5], "Half the worked examples": [24.0, 27.5, 22.0, 26.0, 25.5],
    "Worked examples": [17.5, 21.0, 19.0, 18.0, 20.5],
}
STEPS = [0, 200, 400, 600, 800, 1000]
WRONG_DURING_TRAINING = {  # wrong answers at each training step, one list per run
    "Worked examples": [[31.0, 25.5, 21.0, 19.5, 18.0, 17.5], [30.5, 26.5, 23.0, 20.5, 19.5, 18.5],
                        [31.5, 24.0, 20.5, 18.0, 17.0, 17.0], [31.0, 27.0, 22.5, 21.0, 19.0, 18.5],
                        [30.5, 25.0, 21.5, 19.0, 18.5, 17.5]],
    "Plain fine-tune": [[31.0, 31.5, 32.5, 32.0, 33.0, 33.5], [30.5, 32.0, 31.5, 33.0, 32.5, 33.0],
                        [31.5, 30.5, 32.0, 32.5, 33.5, 32.5], [31.0, 31.0, 33.0, 32.0, 32.0, 34.0],
                        [30.5, 32.5, 32.0, 33.5, 33.0, 33.0]],
}
WRONG_WITH_SEARCH_BY_TOPIC = {  # the topics of WRONG_BY_TOPIC, answered with search
    "Software versions": 15, "Exchange rates": 13, "Product prices": 11, "Sports results": 10, "Company leaders": 9,
    "World records": 9, "Election results": 8, "Movie casts": 6, "Chemistry": 5, "Recipes": 5, "Geography": 4,
    "Classic novels": 3,
}
ANSWER_WORDS = {"Closed book": lognormal(400, 85, 0.45, 1), "With search": lognormal(400, 150, 0.35, 2)}
SECONDS = {"Closed book": lognormal(200, 3, 0.4, 23, 1), "Search snippets": lognormal(200, 6, 0.45, 24, 1),
           "Full documents": lognormal(200, 9.5, 0.5, 48, 1)}  # seconds to answer each of 200 questions


# The gallery is a set of templates grouped by the question a figure answers. This order numbers the files
# (docs/gallery/NN_name.png) and lays out examples/README.md and the README's gallery.
SECTIONS = [
    ("Compare conditions", "One number per condition, or per model and condition, with its interval.",
     ["hbar", "bars", "bars_runs", "dotplot", "dumbbell"]),
    ("Show change over training", "A measure over training steps, doses or compute.", ["line_runs"]),
    ("Show a distribution", "Many values per condition, such as answer lengths, times or scores per item.",
     ["histogram", "box", "strip"]),
    ("Show a relationship", "Two measures against each other, or models against conditions.", ["scatter", "heatmap"]),
    ("Show where outcomes went", "Shares that add up to 100%.", ["stacked"]),
    ("Show what the model did", "Replies and transcripts, as text.", ["quotes", "episodes"]),
    ("Lay out several figures", "Panels that share one legend, for a paper figure or a slide.", ["panels"]),
]
ORDER = [name for _, _, names in SECTIONS for name in names]
STEM = {name: f"{i:02d}_{name}" for i, name in enumerate(ORDER, 1)}  # the file each template is saved to

# What each template is for: its heading in examples/README.md and its caption in the README's gallery.
ABOUT = {
    "hbar": "Rates by condition, the baseline and the intervention named by role",
    "bars": "Each model with and without the intervention",
    "bars_runs": "The mean over runs, with every run as a dot",
    "dotplot": "An effect and its interval for each model, against zero",
    "dumbbell": "Before and after for each model",
    "line_runs": "A training curve, with every run faint behind the mean",
    "histogram": "Two distributions overlaid",
    "box": "Distributions per condition, for many items each",
    "strip": "One dot per item, with the mean and its interval",
    "scatter": "One dot per dataset, against a reference line",
    "heatmap": "Models by conditions",
    "stacked": "Where the outcomes went (coral is the bad outcome)",
    "quotes": "One prompt and contrasting replies",
    "episodes": "What the model did, transcripts side by side",
    "panels": "Several comparisons that share one legend",
}


def figures() -> dict[str, viz.Figure]:
    F: dict[str, viz.Figure] = {}
    F["hbar"] = viz.hbar(
        {"Closed book": 41.0, "Search snippets": 63.5, "Full documents": 88.0}, highlight="Full documents", decimals=0,
        roles={"baseline": "Closed book", "intervention": "Full documents"},
        notes={"Closed book": "164 of 400", "Search snippets": "254 of 400", "Full documents": "352 of 400"},
        title="Full documents raised correct answers from 41% to 88%")
    F["bars"] = viz.bars(
        WRONG_BY_MODEL, series=["Closed book", "With search"], decimals=0, ylabel="Questions answered wrong", frame="blog",
        roles={"baseline": "Closed book", "intervention": "With search"},
        title="Search cut wrong answers for all ten models")
    F["bars_runs"] = viz.bars(
        {arm: sum(runs) / len(runs) for arm, runs in WRONG_BY_SEED.items()}, runs=WRONG_BY_SEED,
        roles={"baseline": "Plain fine-tune", "intervention": "Worked examples"}, ref=31, ref_label="Base model",
        decimals=0, ylabel="Questions answered wrong",
        title="Worked examples cut wrong answers from 34% to 19% in every run")
    F["dotplot"] = viz.dotplot(
        {m: b - a for m, (a, b) in WRONG_BY_MODEL.items()},
        ci={m: diff_ci(a, b, 200) for m, (a, b) in WRONG_BY_MODEL.items()}, ref=0, unit="", decimals=0,
        xlabel="Change in wrong answers with search (percentage points)",
        title="Search cut each model's wrong answers by 8 to 46 points")
    F["line_runs"] = viz.line(
        {arm: mean_curve(runs) for arm, runs in WRONG_DURING_TRAINING.items()}, x=STEPS, runs=WRONG_DURING_TRAINING,
        roles={"baseline": "Plain fine-tune", "intervention": "Worked examples"}, markers=False, decimals=0,
        xlabel="Training step", title="Worked examples cut wrong answers from 31% to 18% during training")
    small = {"unit": "%", "decimals": 0, "ylabel": "Wrong answers", "ticks": [0, 10, 20, 30, 40, 50]}
    prompts = {"Closed book": 38.5, "Longer prompt": 36.0, "Careful prompt": 35.2, "Search": 9.5}
    bigger = {"Small model": 38.5, "Twice the size": 27.0, "Small with search": 9.5, "Both": 7.8}
    index = {"Closed book": 38.5, "Year-old index": 24.0, "Month-old": 13.1, "Week-old": 10.2, "Live index": 9.5}
    empty = {"Closed book": 38.5, "Search answered": 9.5, "Search found nothing": 31.0}
    F["panels"] = viz.panels([
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
        frame="blog", title="Search cut wrong answers more than better prompts or a bigger model")
    F["heatmap"] = viz.heatmap(
        FINISHED, cols=["Small", "Medium", "Large", "Huge"], col_groups=[("Long tasks", ["Large", "Huge"])],
        title="Three of eight models finished most of the huge tasks")
    F["scatter"] = viz.scatter(
        SEARCHES, xunit="%", xticks=[0, 10, 20, 30, 40, 50, 60, 70], yticks=[0, 10, 20, 30, 40, 50, 60, 70, 80],
        labels=["Tech News", "Election Facts", "Health FAQ", "Sports Desk", "Recipe Box"],
        diagonal="one search per question that needs one",
        annotations=[(2, 76, "Above the line: more searches than\nquestions that needed them")],
        xlabel="Share of questions that need recent facts", ylabel="Searches per 100 questions",
        title="Datasets with more questions about recent events drew more searches")
    F["dumbbell"] = viz.dumbbell(
        RATINGS, series=("Closed book", "With search"), unit="", decimals=1, ticks=[1, 2, 3, 4, 5, 6, 7],
        roles={"baseline": "Closed book", "intervention": "With search"},
        missing="not rated", title="Every rated model got higher helpfulness ratings with search")
    F["stacked"] = viz.stacked(
        {"Closed book": [41, 0, 59], "With search": [76, 12, 12]}, series=["Right", "Said it didn’t know", "Wrong"],
        colors=["blue", "beige", "coral"],
        title="With search, wrong answers fell from 59% to 12%")
    F["histogram"] = viz.histogram(
        ANSWER_WORDS, stat="percent", roles={"baseline": "Closed book", "intervention": "With search"}, xlabel="Answer length (words)", ylabel="Share of answers",
        title="With search, the median answer grew from 84 to 150 words")
    F["box"] = viz.box(
        SECONDS, roles={"baseline": "Closed book", "intervention": "Full documents"}, unit="", decimals=1,
        ylabel="Seconds to answer", title="Full documents raised the median answer time from 2.9 to 9.2 seconds")
    F["strip"] = viz.strip(
        {"Closed book": list(WRONG_BY_TOPIC.values()), "With search": list(WRONG_WITH_SEARCH_BY_TOPIC.values())},
        ci=True, roles={"baseline": "Closed book", "intervention": "With search"}, decimals=0, ylabel="Wrong answers per topic",
        title="Search cut wrong answers from 28% to 8% for the average topic")
    F["quotes"] = viz.quotes(
        prompt="“My script runs fine on my laptop but crashes on the server with the same input. What should I check?”",
        replies=[viz.Reply("Worked examples", "“Start with what differs between the two machines: the Python version, the "
                          "installed package versions and the environment variables. Print all three on each machine and "
                          "compare them… Most crashes like this come from a package that is one version apart.”",
                          "trained on step-by-step answers", "intervention"),
                 viz.Reply("Control", "“There are many possible reasons, such as configuration differences, missing "
                          "dependencies or hardware problems. Check the server logs for error messages… You could also "
                          "try reinstalling your dependencies.”", "plain fine-tune", "control")],
        title="The trained model narrowed the problem down instead of listing causes")
    F["episodes"] = viz.episodes([
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
        frame="blog", title="With search, the model checked the release notes instead of guessing")
    return {STEM[k]: F[k] for k in ORDER}


def build(out: Path, only: list[str] | None = None) -> list[Path]:
    out.mkdir(parents=True, exist_ok=True)
    written = []
    for name, fig in figures().items():
        if only and not any(o in name for o in only):
            continue
        written.append(fig.save(out / f"{name}.png"))
    return written


def anchor(heading: str) -> str:
    """The id GitHub gives a markdown heading: lowercase, punctuation dropped, spaces as hyphens."""
    return re.sub(r"[^\w\- ]", "", heading.lower()).replace(" ", "-")


def overview(images: str, link: str, cols: int = 3) -> str:
    """The templates as a grid of thumbnails under their section titles, each linking to its code."""
    out = ["<table>"]
    for title, about, names in SECTIONS:
        out.append(f'<tr><td colspan="{cols}"><b><a href="{link}#{anchor(title)}">{title}</a></b> · {about}</td></tr>')
        for k in range(0, len(names), cols):
            cells = [f'<td width="{100 // cols}%" valign="top"><a href="{link}#{anchor(ABOUT[n])}">'
                     f'<img src="{images}/{STEM[n]}.png" alt="{ABOUT[n]}"></a><br>{ABOUT[n]}</td>'
                     for n in names[k:k + cols]]
            out.append("<tr>" + "".join(cells) + "</tr>")
    out.append("</table>")
    return "\n".join(out)


README_START, README_END = "<!-- gallery: generated from src/viz/gallery.py -->", "<!-- /gallery -->"


def readme_gallery() -> str:
    """The README's gallery: the overview, linking into examples/README.md."""
    return f"{README_START}\n{overview('docs/gallery', 'examples/README.md')}\n{README_END}"


def update_readme(path: Path) -> None:
    s = path.read_text()
    a, b = s.index(README_START), s.index(README_END) + len(README_END)
    path.write_text(s[:a] + readme_gallery() + s[b:])


def examples() -> str:
    """examples/README.md: the templates by section, each with the code that makes it, generated from this file."""
    import ast
    src = Path(__file__).read_text()
    tree = ast.parse(src)
    shared = {t.id for n in tree.body if isinstance(n, ast.Assign) for t in n.targets if isinstance(t, ast.Name)}
    shared |= {n.name for n in tree.body if isinstance(n, ast.FunctionDef)} - {"figures", "build", "examples"}
    fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "figures")
    code_of: dict[str, list[str]] = {}
    pending: list[ast.stmt] = []
    for stmt in fn.body:
        target = stmt.targets[0] if isinstance(stmt, ast.Assign) else None
        if not (isinstance(target, ast.Subscript) and isinstance(target.slice, ast.Constant)):
            if not (isinstance(stmt, ast.AnnAssign) or isinstance(stmt, ast.Return)):
                pending.append(stmt)
            continue
        name = target.slice.value
        nodes = [*pending, stmt.value]
        used = sorted({n.id for s in nodes for n in ast.walk(s) if isinstance(n, ast.Name)} & shared)
        lines = ["import viz"] + ([f"from viz.gallery import {', '.join(used)}"] if used else []) + [""]
        def code(node) -> str:  # the source, its continuation lines moved out of figures()'s body
            first, *rest = ast.get_source_segment(src, node).split("\n")
            return "\n".join([first, *(ln[4:] if ln.startswith("    ") else ln for ln in rest)])
        lines += [code(s) for s in pending]
        lines.append(f'{code(stmt.value)}.save("{name}.png")')
        code_of[name] = lines
        pending = []
    out = ["# viz examples", "",
           "Every figure here is a template: find the question your figure answers, copy its code and change the",
           "numbers. Every number is made up, and error bars and bands are 95% intervals. Run one with",
           "`uv run --with-editable \"$(viz path)\" python ex.py`. This page is generated from `src/viz/gallery.py`",
           "(`viz gallery --examples examples/README.md`), so edit that file, not this one.", "",
           overview("../docs/gallery", ""), ""]
    for title, about, names in SECTIONS:
        out += [f"## {title}", "", about, ""]
        for name in names:
            out += [f"### {ABOUT[name]}", "", f"![{name}](../docs/gallery/{STEM[name]}.png)", "", "```python",
                    *code_of[name], "```", ""]
    out += ["## No Python: a JSON spec", "", "A list of specs makes several figures; each takes the same keys as the",
            "chart's arguments, plus `\"chart\"`, `\"roles\"` and `\"out\"`.", "", "```json",
            '{"chart": "hbar", "data": {"Closed book": 59, "With search": 12},',
            ' "roles": {"baseline": "Closed book", "intervention": "With search"},',
            ' "title": "With search, wrong answers fell from 59% to 12%"}', "```", "",
            "```bash", "viz check fivefold.json && viz render fivefold.json -o fivefold.png --alt", "```", ""]
    return "\n".join(out)

if __name__ == "__main__":
    args = sys.argv[1:]
    if "--examples" in args:
        i = args.index("--examples")
        Path(args[i + 1]).write_text(examples())
        del args[i:i + 2]
    for p in build(Path(args[0] if args else "viz-gallery"), args[1:] or None):
        print(p)
