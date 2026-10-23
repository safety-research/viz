"""The gallery: the templates in examples/, grouped by the question a figure answers.

Each template is a short script that makes one figure and saves it (examples/NN_name.py). This module runs them
to render the gallery and writes the two pages that show them:

    viz gallery -o docs/gallery --examples examples/README.md --readme README.md
"""
from __future__ import annotations

import ast
import re
import runpy
from pathlib import Path

import viz

EXAMPLES = Path(__file__).resolve().parents[2] / "examples"  # the templates live in the clone, beside src/

# The templates by the question a figure answers. This order numbers their files (examples/NN_name.py and
# docs/gallery/NN_name.png) and lays out examples/README.md and the README's gallery.
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
STEM = {name: f"{i:02d}_{name}" for i, name in enumerate(ORDER, 1)}


def template(name: str) -> Path:
    path = EXAMPLES / f"{STEM[name]}.py"
    if not path.is_file():
        raise FileNotFoundError(f"no template {path}: the gallery runs from a viz clone")
    return path


def about(name: str) -> str:
    """What a template is for, from its docstring: its heading on the examples page and its gallery caption."""
    return (ast.get_docstring(ast.parse(template(name).read_text())) or name).split("\n")[0].rstrip(".")


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
    for title, blurb, names in SECTIONS:
        out.append(f'<tr><td colspan="{cols}"><b><a href="{link}#{anchor(title)}">{title}</a></b> · {blurb}</td></tr>')
        for k in range(0, len(names), cols):
            cells = [f'<td width="{100 // cols}%" valign="top"><a href="{link}#{anchor(about(n))}">'
                     f'<img src="{images}/{STEM[n]}.png" alt="{about(n)}"></a><br>{about(n)}</td>'
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
    """examples/README.md: the templates by section, each with its image and code."""
    out = ["# viz examples", "",
           "Every figure here is a template: a short script in this folder that makes it. Find the question your",
           "figure answers, copy its script and change the numbers. Every number is made up, and error bars and",
           "bands are 95% intervals. Run one with `uv run --with-editable \"$(viz path)\" python 01_hbar.py`.",
           "This page is generated from the scripts (`viz gallery --examples examples/README.md`), so edit them,",
           "not this page.", "", overview("../docs/gallery", ""), ""]
    for title, blurb, names in SECTIONS:
        out += [f"## {title}", "", blurb, ""]
        for name in names:
            out += [f"### {about(name)}", "", f"![{name}](../docs/gallery/{STEM[name]}.png)", "",
                    f"[`{STEM[name]}.py`]({STEM[name]}.py)", "", "```python", code(name), "```", ""]
    return "\n".join(out)
