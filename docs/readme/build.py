"""Build the README's landing images from real viz figures: the hero, the buttons and the row of examples.

    uv run python docs/readme/build.py

Every number is made up. The figures go through viz like any other; this script only lays them out in HTML and
renders that to PNG with viz's own fonts.
"""
from __future__ import annotations

import random
from pathlib import Path

import viz
from viz.render import render_html

OUT = Path(__file__).parent
viz.set_defaults(checks="off")  # the cards carry their labels outside the figure, so these figures have no title

# ---------------------------------------------------------------------------------------------- the four examples

COMPUTE = [1e20, 2e20, 5e20, 1e21, 2e21, 5e21, 1e22, 2e22, 5e22, 1e23]
ACCURACY = {"Large model": [31, 36, 42, 47, 53, 59, 64, 69, 74, 78],
            "Medium model": [28, 32, 36, 40, 44, 48, 51, 55, 58, 61],
            "Small model": [25, 28, 31, 33, 36, 38, 40, 42, 44, 46]}


def band(vals, half):
    return [v - half for v in vals], [v + half for v in vals]


def clusters(seed: int = 7, n: int = 220) -> dict[str, list[tuple[float, float]]]:
    rng = random.Random(seed)
    centers = {"Refusal": (-1.0, -0.8, 0.42), "Compliance": (0.2, 1.3, 0.38), "Clarification": (1.5, -1.0, 0.36)}
    return {k: [(rng.gauss(cx, s), rng.gauss(cy, s)) for _ in range(n)] for k, (cx, cy, s) in centers.items()}


SCORES = {"Model A": [86, 59, 89, 92], "Model B": [79, 48, 85, 88], "Model C": [71, 39, 80, 83],
          "Model D": [64, 31, 74, 77], "Model E": [55, 26, 68, 70]}
BENCHMARKS = ["MMLU", "GPQA", "HellaSwag", "ARC"]


def examples(width: float, thumb: bool = False) -> dict[str, viz.Figure]:
    """thumb=True: the bare marks for the hero's cards (no legends or end labels; the cards hide all text)."""
    return {
        "Scaling performance": viz.line(
            ACCURACY, x=COMPUTE, xscale="log", bands={k: band(v, 3) for k, v in ACCURACY.items()}, decimals=0,
            ylabel="Accuracy (%)", xlabel="Compute (FLOPs)", ticks=[0, 20, 40, 60, 80], end_labels=False,
            legend=False if thumb else None, height=230, width=width),
        "Human evaluations": viz.bars(
            {"Helpful": 53, "Harmless": 72, "Honest": 49}, ci={"Helpful": (47, 59), "Harmless": (67, 77),
                                                              "Honest": (44, 55)},
            colors=["coral", "blue", "sage"], sort=False, decimals=0, ylabel="Win rate (%)",
            ticks=[0, 20, 40, 60, 80], height=230, width=width),
        "Representation structure": viz.scatter(
            clusters(), xlabel="PC 1", ylabel="PC 2", xticks=[-2, 0, 2], yticks=[-2, 0, 2], height=250, width=width,
            legend=False if thumb else None),
        "Cross-model comparison": viz.heatmap(
            SCORES, cols=BENCHMARKS, scale="coral", cell_height=26, width=width),
    }


# ---------------------------------------------------------------------------------------------- page pieces

PAPER, INK, MUTED, RULE = "#F7F6F2", "#191918", "#6E6C65", "#E2DFD7"
SERIF, SANS = "Newsreader, Georgia, serif", "'DM Sans', Helvetica, Arial, sans-serif"


def hero() -> str:
    thumbs = examples(260, thumb=True)
    order = ["Representation structure", "Scaling performance", "Human evaluations", "Cross-model comparison"]
    cards = "".join(f'<div class="card">{thumbs[k].svg()}</div>' for k in order)
    return f"""
<style>
.hero{{display:flex;align-items:center;justify-content:space-between;background:{PAPER};padding:64px 56px 44px;
  border-radius:16px;color:{INK}}}
.left{{width:640px}}
.left h1{{font:600 120px/1 {SERIF};letter-spacing:-3px;margin:0 0 14px}}
.left h2{{font:400 34px/1.15 {SERIF};margin:0 0 22px;color:#2C2B28;white-space:nowrap}}
.left p{{font:400 19px/1.55 {SERIF};color:{MUTED};margin:0}}
.right{{width:470px;display:flex;flex-direction:column;align-items:center}}
.fan{{display:flex;perspective:1200px;height:300px;align-items:center;padding-left:30px}}
.card{{width:132px;height:228px;background:#FDFCFA;border:1px solid #DCD8CF;border-radius:6px;
  box-shadow:0 14px 30px rgba(40,34,22,.10);transform:rotateY(-34deg);margin-left:-26px;overflow:hidden;
  display:flex;align-items:center;justify-content:center}}
.card svg{{width:100%;height:auto}}
.card svg text{{display:none}}
.card svg > rect:first-of-type{{fill:#FDFCFA}}
.tags{{margin-top:30px;font:500 11px/1 {SANS};letter-spacing:.34em;color:#8B877E}}
</style>
<div class="hero">
  <div class="left">
    <h1>viz</h1>
    <h2>A data visualization library for AI research.</h2>
    <p>Consistent, publication-quality figures with one call per chart. Color roles, sizes for screens, slides and
    papers, and built-in checks keep every figure clear, accessible and reproducible.</p>
  </div>
  <div class="right">
    <div class="fan">{cards}</div>
    <div class="tags">CONSISTENT &nbsp;·&nbsp; HIGH QUALITY &nbsp;·&nbsp; REPRODUCIBLE</div>
  </div>
</div>"""


def row() -> str:
    figs = examples(236)
    cards = "".join(f'<div class="ex"><div class="h">{name}</div>{fig.svg()}</div>' for name, fig in figs.items())
    return f"""
<style>
.row{{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;padding:2px;background:#fff}}
.ex{{border:1px solid {RULE};border-radius:10px;padding:18px 12px 8px;background:#fff}}
.ex .h{{font:400 21px/1.2 {SERIF};color:{INK};margin:0 0 4px 10px}}
.ex svg{{width:100%;height:auto;display:block}}
</style>
<div class="row">{cards}</div>"""


def button(label: str, dark: bool) -> str:
    bg, fg, border = (INK, "#FFFFFF", INK) if dark else ("#F1EFEA", INK, "#DCD8CF")
    return (f'<div style="display:inline-block;padding:1px">'
            f'<div style="display:inline-block;background:{bg};color:{fg};border:1px solid {border};border-radius:8px;'
            f'padding:12px 24px;font:600 16px/1 {SANS}">{label}</div></div>')


ICONS = {  # 24 x 24 line icons, drawn here so the README needs no icon font
    "consistent": '<rect x="3.5" y="3.5" width="17" height="17" rx="1.5"/><path d="M3.5 9.2h17M3.5 14.8h17M9.2 3.5v17M14.8 3.5v17"/>',
    "quality": '<path d="M4 20h16"/><path d="M6 16.5 15.8 6.7a2 2 0 0 1 2.8 2.8L8.8 19.3 5 20l1-3.5z"/>',
    "research": '<path d="M6.5 2.8h8l4 4v14.4h-12z"/><path d="M14.5 2.8v4h4M9.3 11.5h6.4M9.3 14.5h6.4M9.3 17.5h4"/>',
    "productive": '<path d="M13.2 2.5 5 13.6h6.2l-1 7.9 8.3-11.2h-6.3z"/>',
}


def main() -> None:
    render_html(hero(), OUT / "hero.png", 1200)
    render_html(row(), OUT / "examples.png", 1200)
    render_html(button("Get started &nbsp;→", True), OUT / "get-started.png", 400, fit=True)
    render_html(button("View examples", False), OUT / "view-examples.png", 400, fit=True)
    for name, paths in ICONS.items():
        (OUT / f"icon-{name}.svg").write_text(
            f'<svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" '
            f'stroke="{INK}" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round">{paths}</svg>\n')
    for p in sorted(OUT.glob("*.png")):
        print(p)


if __name__ == "__main__":
    main()
