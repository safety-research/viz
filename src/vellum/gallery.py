"""Example gallery: one figure per chart type, with made-up numbers and no subtitles.

    vellum gallery -o out/      or      python -m vellum.gallery out/
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import vellum as vl


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return 100 * (c - h), 100 * (c + h)


def wilson_cis(rates: dict[str, float], n: int) -> dict[str, tuple[float, float]]:
    """Wilson intervals for percents that were each measured on n items."""
    return {k: wilson(round(v * n / 100), n) for k, v in rates.items()}


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
PREFERENCES = [("Model A", 172, 78), ("Model B", 150, 95), ("Model C", 201, 64), ("Model D", 133, 112),
               ("Model E", 188, 70), ("Model F", 160, 90)]  # blind comparisons won, lost
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
TOOL = ("Search the project's documentation and return the three most relevant passages, each with its page title "
        "and link. Use it when an answer depends on details you are not sure of, such as version numbers, settings or "
        "recent changes. Write the query the way the documentation would phrase it.")


def figures() -> dict[str, vl.Figure]:
    F: dict[str, vl.Figure] = {}
    F["01_hbar_sorted"] = vl.hbar(
        WRONG_BY_TOPIC, sort=True, color="coral", decimals=0,
        title="Questions on fast-changing topics were answered wrong most often")
    F["02_hbar_highlight"] = vl.hbar(
        {"Closed book": 41.0, "Search snippets": 63.5, "Full documents": 88.0},
        highlight="Full documents", decimals=0,
        notes={"Closed book": "164 of 400", "Search snippets": "254 of 400", "Full documents": "352 of 400"},
        title="Full documents raised correct answers from 41% to 88%")
    F["03_tiles"] = vl.tiles(
        [[vl.Tile(412, ["agreed the answer was right", "94% of the answers people accepted"], "blue", strong=True),
          vl.Tile(38, ["accepted a wrong answer", "the costly mistake"], "coral")],
         [vl.Tile(27, ["rejected a right answer", "mostly unusual formats"], "beige"),
          vl.Tile(523, ["agreed the answer was wrong"], "gray")]],
        col_headers=[("People said right", "439 answers"), ("People said wrong", "561 answers")],
        row_headers=[("Grader said right", "450 answers"), ("Grader said wrong", "550 answers")],
        title="The automatic grader agreed with people on 935 of 1,000 answers")
    F["04_scatter"] = vl.scatter(
        SEARCHES, xunit="%", xticks=[0, 10, 20, 30, 40, 50, 60, 70], yticks=[0, 10, 20, 30, 40, 50, 60, 70, 80],
        labels=["Tech News", "Election Facts", "Health FAQ", "Sports Desk", "Recipe Box"],
        diagonal="one search per question that needs one",
        annotations=[(2, 76, "Above the line: more searches than\nquestions that needed them")],
        xlabel="Share of questions that need recent facts", ylabel="Searches per 100 questions",
        title="Datasets with more questions about recent events drew more searches")
    F["05_heatmap"] = vl.heatmap(
        FINISHED, cols=["Small", "Medium", "Large", "Huge"], col_groups=[("Long tasks", ["Large", "Huge"])],
        title="Three of eight models finished most of the huge tasks")
    F["06_panels_grouped"] = vl.panels([
        vl.hbar({"Recent events": [3.10, 5.45], "Settled facts": [5.60, 5.72]}, series=["Closed book", "With search"],
                unit="", decimals=1, domain=(1, 7), ticks=[1, 2, 3, 4, 5, 6, 7], title="Helpfulness, 1 to 7"),
        vl.hbar({"Recent events": [31.5, 74.0], "Settled facts": [80.5, 82.0]}, series=["Closed book", "With search"],
                decimals=0, title="Would ask it again")],
        title="With search, people rated answers on recent events higher")
    F["07_hbar_notes"] = vl.hbar(
        {"Wrong answer": 2.31, "Said it didn’t know": 3.94, "Right answer with a source": 5.86},
        colors={"Wrong answer": "coral", "Said it didn’t know": "blue", "Right answer with a source": "gray"},
        notes={"Wrong answer": "412 chats", "Said it didn’t know": "236 chats", "Right answer with a source": "1,052 chats"},
        unit="", decimals=1, ticks=[1, 2, 3, 4, 5, 6, 7],
        title="People rated “I don’t know” higher than a wrong answer")
    F["08_hbar_sections"] = vl.hbar(
        [("Base model", 31.0), ("Plain fine-tune (control)", 33.5), ("Worked examples", 18.2), vl.section("Other data"),
         ("Textbook passages", 27.4), ("Forum answers", 36.9), ("Short answers only", 22.6)],
        roles={"reference": "Base model", "intervention": "Worked examples"}, highlight="Worked examples", decimals=0,
        ref=31.0, notes={"Forum answers": "worse than the base model"},
        title="Worked examples cut wrong answers from 31% to 18%")
    F["09_quotes"] = vl.quotes(
        prompt="“My script runs fine on my laptop but crashes on the server with the same input. What should I check?”",
        replies=[vl.Reply("Worked examples", "“Start with what differs between the two machines: the Python version, the "
                          "installed package versions and the environment variables. Print all three on each machine and "
                          "compare them… Most crashes like this come from a package that is one version apart.”",
                          "trained on step-by-step answers", "blue"),
                 vl.Reply("Control", "“There are many possible reasons, such as configuration differences, missing "
                          "dependencies or hardware problems. Check the server logs for error messages… You could also "
                          "try reinstalling your dependencies.”", "plain fine-tune", "gray")],
        title="The trained model narrowed the problem down instead of listing causes")
    F["10_code_card"] = vl.code_card("search_docs", {"query": "What to look up, in a few words."}, TOOL)
    small = {"unit": "%", "decimals": 0, "ylabel": "Wrong answers", "ticks": [0, 10, 20, 30, 40, 50]}
    prompts = {"Closed book": 38.5, "Longer prompt": 36.0, "Careful prompt": 35.2, "Search": 9.5}
    bigger = {"Small model": 38.5, "Twice the size": 27.0, "Small with search": 9.5, "Both": 7.8}
    index = {"Closed book": 38.5, "Year-old index": 24.0, "Month-old": 13.1, "Week-old": 10.2, "Live index": 9.5}
    empty = {"Closed book": 38.5, "Search answered": 9.5, "Search found nothing": 31.0}
    F["11_small_multiples"] = vl.panels([
        vl.bars(prompts, ci=wilson_cis(prompts, 1200),
                title="(a) Better prompts", **small),
        vl.bars(bigger, ci=wilson_cis(bigger, 1200),
                title="(b) A bigger model", **small),
        vl.bars(index, ci=wilson_cis(index, 1200),
                title="(c) Search index age", **small),
        vl.bars(empty, ci=wilson_cis(empty, 1200), colors={"Search found nothing": "light-blue"},
                title="(d) When search finds nothing", **small)],
        legend={"Closed book": "coral", "Other fixes": "gray", "Search": "blue", "Search that finds nothing": "light-blue"},
        roles={"baseline": ["Closed book", "Small model"],
               "intervention": ["Search", "Small with search", "Both", "Year-old index", "Month-old", "Week-old",
                                "Live index", "Search answered"]},
        frame="blog", title="Search cut wrong answers more than better prompts or a bigger model")
    shares = {m: 100 * won / (won + lost) for m, won, lost in PREFERENCES}
    cis = {m: wilson(won, won + lost) for m, won, lost in PREFERENCES}
    all_won, all_lost = sum(p[1] for p in PREFERENCES), sum(p[2] for p in PREFERENCES)
    shares["Pooled"], cis["Pooled"] = 100 * all_won / (all_won + all_lost), wilson(all_won, all_won + all_lost)
    F["12_blog_panels"] = vl.panels([
        vl.bars({"Search − closed book": 0.12, "Rerank − closed book": 0.19, "Rerank − search": 0.07},
                ci={"Search − closed book": (-0.15, 0.39), "Rerank − closed book": (-0.06, 0.44),
                    "Rerank − search": (-0.21, 0.33)},
                colors=["sage", "sage", "light-sage"], unit="", decimals=2, signed=True, ticks=[-0.4, -0.2, 0, 0.2, 0.4, 0.6],
                ylabel="Difference in rating (−3 to +3 scale)", title="User ratings"),
        vl.bars(shares, ci=cis, colors={"Pooled": "deep-sage"}, color="sage", decimals=0, ref=50, ticks=[0, 25, 50, 75, 100],
                ylabel="Prefers the search version", title="Blind comparisons")],
        title="Search won 66% of blind comparisons but did not clearly change ratings", frame="blog", legend=False)
    F["13_episodes"] = vl.episodes([
        vl.Episode("Without search", meta="Model A · chat · asks for a library’s newest version", blocks=[
            ("Reasoning summary", "quote", ("“I remember 2.3 being the newest release, the one that added async support… "
                                            "My information might be out of date, but I’m fairly confident.”")),
            ("Answer", "code", "“The newest version is 2.3. Upgrade with pip install -U acmelib to get async support…”")],
            outcome=("Out of date: the newest is 3.0", "coral")),
        vl.Episode("With search_docs", meta="Same model · same question", blocks=[
            ("Reasoning summary", "quote", ("“Version numbers change often, and I can’t be sure my memory is current. "
                                            "I should check the release notes.”")),
            ("search_docs", "code", "“query: acmelib release notes, newest version”")],
            outcome=("Answered 3.0, with a link", "blue"))],
        frame="blog", title="With search, the model checked the release notes instead of guessing")
    F["14_bars_models"] = vl.bars(
        WRONG_BY_MODEL, series=["Closed book", "With search"], decimals=0, ylabel="Questions answered wrong", frame="blog",
        title="Search cut wrong answers for all ten models")
    F["15_dumbbell"] = vl.dumbbell(
        RATINGS, series=("Closed book", "With search"), unit="", decimals=1, ticks=[1, 2, 3, 4, 5, 6, 7],
        missing="not rated", title="Every rated model got higher helpfulness ratings with search")
    F["16_waffle"] = vl.waffle(
        {"Out-of-date fact": 210, "Misread the question": 140, "Arithmetic slip": 90, "Grader error": 60},
        count_label="answers",
        title="Out-of-date facts caused 42 in 100 wrong answers")
    F["17_line_example"] = vl.line(
        {"Worked examples": [31, 26, 21, 17], "Plain fine-tune": [31, 32, 33, 34]}, x=[0, 1, 3, 10],
        xtick_labels={0: "0", 1: "1M", 3: "3M", 10: "10M"}, xscale="category",
        roles={"baseline": "Plain fine-tune", "intervention": "Worked examples"},
        bands={"Worked examples": ([27, 22, 17, 13], [35, 30, 25, 21])}, xlabel="Fine-tuning tokens",
        title="Wrong answers fell from 31% to 17% with more worked examples")
    F["18_stacked_example"] = vl.stacked(
        {"Closed book": [41, 0, 59], "With search": [76, 12, 12]}, series=["Right", "Said it didn’t know", "Wrong"],
        colors=["blue", "beige", "coral"],
        title="With search, wrong answers fell from 59% to 12%")
    return F


def build(out: Path, only: list[str] | None = None) -> list[Path]:
    out.mkdir(parents=True, exist_ok=True)
    written = []
    for name, fig in figures().items():
        if only and not any(o in name for o in only):
            continue
        written.append(fig.save(out / f"{name}.png"))
    return written


if __name__ == "__main__":
    for p in build(Path(sys.argv[1] if len(sys.argv) > 1 else "vellum-gallery"), sys.argv[2:] or None):
        print(p)
