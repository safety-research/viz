"""Build figures from plain dicts / JSON, so any script or session can make one without importing helpers.

    {"chart": "hbar", "data": {"Closed book": 59, "With search": 12}, "title": "...", "highlight": "With search"}

Nested specs: panels take {"chart": "panels", "figs": [spec, spec]}; tiles take dict tiles; sections in list
data are {"section": "Other data"}.
"""
from __future__ import annotations

import json
from pathlib import Path


def from_spec(spec: dict):
    from . import CHARTS, Episode, Reply, Tile
    spec = dict(spec)
    kind = spec.pop("chart", None) or spec.pop("type", None)
    if kind not in CHARTS:
        raise ValueError(f"unknown chart {kind!r}; one of: {', '.join(sorted(CHARTS))}")
    spec.pop("out", None)
    if kind == "panels":
        spec["figs"] = [from_spec(f) for f in spec["figs"]]
        figs = spec.pop("figs")
        return CHARTS[kind](figs, **spec)
    if kind == "tiles":
        spec["grid"] = [[Tile(**t) if isinstance(t, dict) else t for t in row] for row in spec["grid"]]
        grid = spec.pop("grid")
        return CHARTS[kind](grid, **spec)
    if kind == "quotes":
        reps = [Reply(**r) if isinstance(r, dict) else Reply(*r) for r in spec.pop("replies")]
        return CHARTS[kind](reps, **spec)
    if kind == "episodes":
        items = []
        for e in spec.pop("items"):
            e = dict(e)
            e["blocks"] = [tuple(b) for b in e.get("blocks", [])]
            if e.get("outcome"):
                e["outcome"] = tuple(e["outcome"])
            items.append(Episode(**e))
        return CHARTS[kind](items, **spec)
    if kind == "code_card":
        return CHARTS[kind](spec.pop("name"), spec.pop("params", None), spec.pop("description", ""), **spec)
    first = {"hbar": "data", "bars": "data", "heatmap": "data", "waffle": "parts", "scatter": "points",
             "dumbbell": "data", "line": "series", "stacked": "data"}[kind]
    return CHARTS[kind](spec.pop(first), **spec)


def render_file(path: str | Path, out: str | Path | None = None, scale: float | None = None,
                figures: bool = False) -> list:
    """Render a JSON file holding one spec or a list of specs (each may carry its own "out").
    Returns the written paths, or (path, Figure) pairs with figures=True."""
    p = Path(path)
    raw = json.loads(p.read_text() if str(path) != "-" else __import__("sys").stdin.read())
    specs = raw if isinstance(raw, list) else [raw]
    written = []
    for i, s in enumerate(specs):
        target = s.get("out") or out or (p.with_suffix(".png") if len(specs) == 1 else p.with_name(f"{p.stem}-{i + 1}.png"))
        if len(specs) > 1 and out and not s.get("out"):
            o = Path(out)
            target = o.with_name(f"{o.stem}-{i + 1}{o.suffix or '.png'}")
        fig = from_spec(s)
        p_ = fig.save(target, scale)
        written.append((p_, fig) if figures else p_)
    return written
