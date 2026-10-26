"""The gallery: the templates in examples/, grouped by the question a figure answers.

Each template is a short script that makes one figure and saves it (examples/NN_name.py). This module runs them
to render the gallery and writes the two pages that show them:

    viz gallery -o docs/gallery --examples examples/README.md --readme README.md
"""
from __future__ import annotations

import ast
import dataclasses
import re
import runpy
from pathlib import Path

import viz
from . import svg as S
from . import theme as th

EXAMPLES = Path(__file__).resolve().parents[2] / "examples"  # the templates live in the clone, beside src/

# The templates by the question a figure answers. This order numbers their files (examples/NN_name.py and
# docs/gallery/NN_name.png) and lays out examples/README.md and the README's gallery.
SECTIONS = [
    ("Comparisons", "Rates across conditions and models, with their intervals.",
     ["hbar", "bars", "bars_runs", "dotplot", "stacked"]),
    ("Training dynamics", "A behavior or reward over training steps.",
     ["line_runs", "line_models", "line_smooth", "line_marks", "area"]),
    ("Evaluations", "Many models on many evals, trade-offs and scaling.",
     ["bars_benchmarks", "table", "heatmap", "scatter", "scatter_frontier", "line_log"]),
    ("Monitors and probes", "How well a monitor, classifier or probe catches a behavior.",
     ["line_roc", "histogram_scores", "tiles", "line_layers"]),
    ("Interpretability", "Inside the model: activations, scores on each token, steering.",
     ["scatter_pca", "tokens", "line_steer"]),
    ("Self-reports and ratings", "What a model says about itself, how judges rate it, and whether the two agree.",
     ["likert", "dumbbell", "mtmm"]),
    ("Distributions", "Many values per condition, such as lengths, times or scores per item.",
     ["histogram", "box", "strip"]),
    ("Transcripts", "What the model said and did.", ["quotes", "episodes", "chat"]),
    ("Multi-panel figures", "Several charts in one figure, with one legend.", ["panels"]),
]
ORDER = [name for _, _, names in SECTIONS for name in names]
STEM = {name: f"{i:02d}_{name}" for i, name in enumerate(ORDER, 1)}


def template(name: str) -> Path:
    path = EXAMPLES / f"{STEM[name]}.py"
    if not path.is_file():
        raise FileNotFoundError(f"no template {path}: the gallery runs from a viz clone")
    return path


def about(name: str) -> str:
    """A template's short name, the first line of its docstring: its card's caption and its heading."""
    return (ast.get_docstring(ast.parse(template(name).read_text())) or name).split("\n")[0].rstrip(".")


def describe(name: str) -> str:
    """What a template shows, the rest of its docstring: the line under its heading on the examples page."""
    return (ast.get_docstring(ast.parse(template(name).read_text())) or "").partition("\n")[2].strip()


def code(name: str) -> str:
    """A template's code as the examples page shows it: everything after the docstring."""
    src = template(name).read_text()
    return "\n".join(src.splitlines()[ast.parse(src).body[0].end_lineno:]).strip("\n")


def figure(name: str) -> viz.Figure:
    """Run a template and return the figure it saves, without saving it."""
    saved: list[viz.Figure] = []
    save, viz.Figure.save = viz.Figure.save, lambda fig, *a, **k: saved.append(fig)
    try:
        runpy.run_path(str(template(name)), run_name="__main__")
    finally:
        viz.Figure.save = save
    if not saved:
        raise ValueError(f"{template(name).name} saves no figure")
    return saved[-1]


def figures() -> dict[str, viz.Figure]:
    """Every template's figure, keyed by its file name, in gallery order."""
    return {STEM[name]: figure(name) for name in ORDER}


CARD_W, CARD_H, CARD_PAD, CARD_NAME = 640, 460, 20, 32  # a gallery card in CSS px, two to a row; its PNG is twice that
CARD_CHART_W = 720  # the width a card lays its chart out at: room for ten groups of bars, then scaled by about 0.83


def card(name: str, fig: viz.Figure | None = None) -> str:
    """A template's gallery card as HTML: its short name over its chart, without the title. The chart is laid out at
    CARD_CHART_W and scaled to fit, so a busy chart keeps room and its text stays readable."""
    fig = dataclasses.replace(fig or figure(name), title=None, subtitle=None, width=CARD_CHART_W)
    svg = fig.svg(background=False)
    w, h = (float(v) for v in re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"', svg).groups())
    scale = min(1.0, (CARD_W - 2 * CARD_PAD) / w, (CARD_H - 2 * CARD_PAD - CARD_NAME * 1.2 - 12) / h)  # the name above
    svg = re.sub(r'width="[\d.]+" height="[\d.]+"', f'width="{w * scale:.1f}" height="{h * scale:.1f}"', svg, count=1)
    return (f'<div style="display:inline-block;padding:1px"><div style="box-sizing:border-box;width:{CARD_W}px;'
            f'height:{CARD_H}px;padding:{CARD_PAD}px;border:1px solid {th.RULE};border-radius:12px;'
            f'background:{th.BG};display:flex;flex-direction:column"><div style="font:400 {CARD_NAME}px/1.2 '
            f'{th.FAMILIES["serif"]};color:{th.INK};margin:0 0 12px 2px">{S.esc(about(name))}</div>'
            f'<div style="flex:1;display:flex;align-items:center;justify-content:center">{svg}</div></div></div>')


def build(out: Path, only: list[str] | None = None) -> list[Path]:
    """Every template's figure as out/NN_name.png, and its gallery card as out/cards/NN_name.png."""
    from .render import render_html
    (out / "cards").mkdir(parents=True, exist_ok=True)
    written = []
    for name in ORDER:
        if only and not any(o in STEM[name] for o in only):
            continue
        fig = figure(name)
        written.append(fig.save(out / f"{STEM[name]}.png"))
        render_html(card(name, fig), out / "cards" / f"{STEM[name]}.png", CARD_W + 2, fit=True, transparent=True)
    return written


def anchor(heading: str) -> str:
    """The id GitHub gives a markdown heading: lowercase, punctuation dropped, spaces as hyphens."""
    return re.sub(r"[^\w\- ]", "", heading.lower()).replace(" ", "-")


def overview(images: str, link: str, heading: str = "###") -> str:
    """The templates as rows of cards under their section names, each card linking to its code. heading="" sets
    the section names in bold instead of as headings."""
    out = []
    for title, blurb, names in SECTIONS:
        out += [f"{heading} {title}" if heading else f"**{title}**", "", blurb, ""]
        out += [f'<a href="{link}#{anchor(about(n))}"><img src="{images}/cards/{STEM[n]}.png" width="49%" '
                f'alt="{about(n)}"></a>' for n in names]
        out.append("")
    return "\n".join(out).rstrip("\n")


README_START, README_END = "<!-- gallery: generated from src/viz/gallery.py -->", "<!-- /gallery -->"


def readme_gallery() -> str:
    """The README's gallery: the overview, linking into examples/README.md."""
    return f"{README_START}\n{overview('docs/gallery', 'examples/README.md')}\n{README_END}"


def update_readme(path: Path) -> None:
    s = path.read_text()
    a, b = s.index(README_START), s.index(README_END) + len(README_END)
    path.write_text(s[:a] + readme_gallery() + s[b:])


def examples() -> str:
    """examples/README.md: the templates by section, each with its image and code."""
    out = ["# viz examples", "",
           "Every figure here is a template: a short script in this folder that makes it. Find the question your",
           "figure answers, copy its script and change the numbers. Every number is made up, and error bars and",
           "bands are 95% intervals. Run one with `viz run 01_hbar.py`.",
           "This page is generated from the scripts (`viz gallery --examples examples/README.md`), so edit them,",
           "not this page.", "", overview("../docs/gallery", "", heading=""), ""]
    for title, blurb, names in SECTIONS:
        out += [f"## {title}", "", blurb, ""]
        for name in names:
            out += [f"### {about(name)}", "", describe(name), "", f"![{about(name)}](../docs/gallery/{STEM[name]}.png)",
                    "", f"[`{STEM[name]}.py`]({STEM[name]}.py)", "", "```python", code(name), "```", ""]
    return "\n".join(out)
