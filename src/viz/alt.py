"""Alt text: a figure's data in words, for screen readers and for the alt attribute of an image in a write-up.

Each chart's arguments are read back through the same normalizers the chart uses, so the text gives exactly the
numbers the figure shows: "Bar chart. Closed book 59%; With search 12%." Figure.alt_text() puts the title first.
"""
from __future__ import annotations

from collections.abc import Mapping

from . import data as D
from . import scale as SC
from .charts.common import UNSET, resolve_unit

MAX_VALUES = 60  # past this, describe the range instead of every value


def _fmt(data_vals, unit=UNSET, decimals=None, fmt=None, signed=False):
    unit, _ = resolve_unit(unit)
    f = SC.formatter(fmt, decimals, unit, signed, [v for v in data_vals if v is not None])
    return lambda v: "no value" if v is None else f(v)


def _rows_text(rows, names, f, notes=None, missing=None) -> str:
    vals = [v for r in rows for v in r.values if v is not None]
    if len(vals) > MAX_VALUES:
        return f"{len(rows)} rows, values from {f(min(vals))} to {f(max(vals))}"
    out, section = [], None
    for r in rows:
        if r.section:
            section = r.label
            continue
        if missing and all(v is None for v in r.values):
            item = f"{r.label} {missing}"
        elif len(r.values) == 1:
            item = f"{r.label} {f(r.values[0])}"
        else:
            nm = names or [f"series {j + 1}" for j in range(len(r.values))]
            item = f"{r.label}: " + ", ".join(f"{n} {f(v)}" for n, v in zip(nm, r.values))
        if notes and notes.get(r.label):
            item += f" ({notes[r.label]})"
        if section:
            item, section = f"{section}: {item}", None
        out.append(item)
    return "; ".join(out)


def _bars(kind):
    def describe(data, series=None, unit=UNSET, decimals=None, fmt=None, signed=False, notes=None, runs=None, **_):
        rows, _ns, names = D.rows(data, series)
        names = list(series) if series is not None else names
        f = _fmt([v for r in rows for v in r.values], unit, decimals, fmt, signed)
        if notes is not None and not isinstance(notes, Mapping):
            notes = {r.label: n for r, n in zip([r for r in rows if not r.section], notes)}
        if isinstance(runs, Mapping):  # one series: list each label's runs after its value
            notes = dict(notes or {})
            for lab, rs in runs.items():
                if rs and not isinstance(rs[0], (list, tuple)):
                    runs_txt = "runs " + ", ".join(f(v) for v in rs if v is not None)
                    notes[lab] = f"{notes[lab]}; {runs_txt}" if notes.get(lab) else runs_txt
        return f"{kind}. {_rows_text(rows, names, f, notes)}."
    return describe


def _dotplot(data, series=None, ci=None, unit=UNSET, decimals=None, fmt=None, signed=False, **_):
    rows, ns, names = D.rows(data, series)
    names = list(series) if series is not None else names
    D.attach_ci(rows, ci, ns)
    f = _fmt([v for r in rows for v in r.values], unit, decimals, fmt, signed)
    parts = []
    for r in rows:
        if r.section:
            continue
        for j, v in enumerate(r.values):
            c = r.ci[j] if r.ci and j < len(r.ci) else None
            who = r.label if ns == 1 else f"{r.label}, {(names or [f'series {k + 1}' for k in range(ns)])[j]}"
            parts.append(f"{who} {f(v)}" + (f" (interval {f(c[0])} to {f(c[1])})" if c else ""))
    return f"Dot plot. {'; '.join(parts)}."


def _distribution(kind: str, flat: str | None, stat: str = "median", default_unit=UNSET):
    def describe(data, series=None, unit=default_unit, decimals=None, fmt=None, **_):
        from .charts.dist import mean, samples, tukey
        labels, vals, ns, _names = samples(data, series, flat_label=flat)
        f = _fmt([v for g in vals for s in g for v in s], unit, decimals, fmt)
        parts = []
        for lab, groups in zip(labels, vals):
            for j, s in enumerate(groups):
                if not s:
                    continue
                name = lab if ns == 1 else f"{lab}, {(series or [f'series {k + 1}' for k in range(ns)])[j]}"
                t = tukey(s)
                centre = f"mean {f(mean(s))}" if stat == "mean" else f"median {f(t.median)}"
                parts.append(f"{name + ': ' if name else ''}{len(s)} values, {centre}, middle half {f(t.q1)} to "
                             f"{f(t.q3)}, range {f(min(s))} to {f(max(s))}")
        return f"{kind}. {'; '.join(parts)}."
    return describe


def _dumbbell(data, series=("Without", "With"), unit=UNSET, decimals=None, fmt=None, missing="doesn't apply", **_):
    rows, _ns, _ = D.rows(data)
    f = _fmt([v for r in rows for v in r.values], unit, decimals, fmt)
    return f"Dumbbell chart, {series[0]} to {series[1]}. {_rows_text(rows, list(series), f, missing=missing)}."


def _stacked(data, series, normalize=False, unit=UNSET, decimals=None, fmt=None, **_):
    rows, _ns, _ = D.rows(data, series)
    rows = [r for r in rows if not r.section]
    if normalize:
        for r in rows:
            t = sum(v or 0 for v in r.values) or 1
            r.values = [None if v is None else 100 * v / t for v in r.values]
    f = _fmt([v for r in rows for v in r.values], unit, decimals, fmt)
    return f"Stacked bars. {_rows_text(rows, list(series), f)}."


def _line(series, x=None, unit=UNSET, decimals=None, fmt=None, xtick_labels=None, xlabel=None, **_):
    from .charts.line import _series
    data = _series(series, x)
    f = _fmt([v for pts in data.values() for _, v in pts], unit, decimals, fmt)
    xl = (lambda v: str(xtick_labels.get(v, v))) if isinstance(xtick_labels, Mapping) else (lambda v: f"{v:g}")
    parts = []
    for nm, pts in data.items():
        pts = [(a, b) for a, b in pts if b is not None]
        if not pts:
            continue
        if len(pts) <= 8:
            parts.append(f"{nm}: " + ", ".join(f"{f(b)} at {xl(a)}" for a, b in pts))
        else:
            parts.append(f"{nm}: from {f(pts[0][1])} at {xl(pts[0][0])} to {f(pts[-1][1])} at {xl(pts[-1][0])}")
    over = f" over {xlabel.lower()}" if xlabel else ""
    return f"Line chart{over}. {'; '.join(parts)}."


def _heatmap(data, rows=None, cols=None, unit=UNSET, decimals=None, fmt=None, signed=False, **_):
    from .charts.heatmap import _matrix
    rl, cl, vals = _matrix(data, rows, cols)
    f = _fmt([v for r in vals for v in r], unit, decimals, fmt, signed)
    if decimals is None and fmt is None and resolve_unit(unit)[0] == "%":  # as the heatmap itself rounds
        f = _fmt([], unit, 0, None, signed)
    flat = [v for r in vals for v in r if v is not None]
    if len(flat) > MAX_VALUES:
        return (f"Heatmap, {len(rl)} rows by {len(cl)} columns ({', '.join(cl)}), values from {f(min(flat))} "
                f"to {f(max(flat))}.")
    body = "; ".join(f"{r}: " + ", ".join(f"{c} {f(v)}" for c, v in zip(cl, vs)) for r, vs in zip(rl, vals))
    return f"Heatmap. {body}."


def _scatter(points, labels=None, xunit="", yunit="", xlabel=None, ylabel=None, **_):
    from .charts.scatter import _groups, _points
    groups = _groups(points)
    if groups is not None:
        axes = ", ".join(s for s in (f"x: {xlabel}" if xlabel else "", f"y: {ylabel}" if ylabel else "") if s)
        parts = [f"{g}: {len(v)} points around ({sum(a for a, _ in v) / len(v):.2g}, {sum(b for _, b in v) / len(v):.2g})"
                 for g, v in groups.items() if v]
        return f"Scatter plot in {len(groups)} groups{' (' + axes + ')' if axes else ''}. {'; '.join(parts)}."
    pts = _points(points)
    named = {p[0] for p in pts} if labels is True else set(labels or [])
    axes = ", ".join(s for s in (f"x: {xlabel}" if xlabel else "", f"y: {ylabel}" if ylabel else "") if s)
    show = pts if len(pts) <= 20 else [p for p in pts if p[0] in named]
    unnamed = lambda lab: lab.startswith("#") and lab[1:].isdigit()  # scatter's name for an unlabeled point
    listed = "; ".join(f"({x:g}{xunit}, {y:g}{yunit})" if unnamed(lab) else f"{lab} ({x:g}{xunit}, {y:g}{yunit})"
                       for lab, x, y in show)
    return f"Scatter plot of {len(pts)} points{' (' + axes + ')' if axes else ''}. {listed}."


def _waffle(parts, total=100, count_label=None, **_):
    items = D.pairs(parts)
    n = sum(v for _, v in items) or 1
    unit = f" {count_label}" if count_label else ""
    body = "; ".join(f"{lab} {round(total * v / n)} in {total} ({v:g}{unit})" for lab, v in items)
    return f"Waffle chart. {body}."


def _tiles(grid, col_headers=None, row_headers=None, **_):
    from .charts.tiles import _fmt as tile_fmt
    from .charts.tiles import _tile
    head = lambda h: (h[0] if isinstance(h, (list, tuple)) else h) if h else None
    out = []
    for i, row in enumerate(grid):
        for j, t in enumerate(row):
            t = _tile(t)
            where = " and ".join(x for x in (head(row_headers[i]) if row_headers else None,
                                              head(col_headers[j]) if col_headers else None) if x)
            out.append(f"{where + ': ' if where else ''}{tile_fmt(t.value)}" + (f" ({', '.join(t.lines)})" if t.lines else ""))
    return f"Number tiles. {'; '.join(out)}."


def _panels(figs, **_):
    parts = [f"{f.title}: {f.meta.get('alt', '')}".strip() if f.title else f.meta.get("alt", "") for f in figs]
    return f"{len(figs)} panels. " + " ".join(p for p in parts if p)


def _quotes(replies, prompt=None, prompt_label="The person", **_):
    from .cards import _reply
    out = [f"{prompt_label}: {prompt}"] if prompt else []
    for r in replies:
        r = _reply(r)
        out.append(f"{r.label}{' (' + r.note + ')' if r.note else ''}: {r.text}")
    return "Quoted replies. " + " ".join(out)


def _episodes(items, **_):
    from .cards import _episode
    out = []
    for e in items:
        e = _episode(e)
        blocks = " ".join(f"{label + ': ' if label else ''}{text}" for label, _kind, text in e.blocks)
        outcome = f" Outcome: {e.outcome[0]}." if e.outcome else ""
        out.append(f"{e.title}{' (' + e.meta + ')' if e.meta else ''}. {blocks}{outcome}")
    return "Transcript excerpts. " + " ".join(out)


def _code_card(name, params=None, description="", **_):
    sig = ", ".join(params or {})
    return f"Tool definition: {name}({sig}). {description}"


DESCRIBERS = {"hbar": _bars("Horizontal bar chart"), "bars": _bars("Bar chart"), "dumbbell": _dumbbell,
              "stacked": _stacked, "line": _line, "heatmap": _heatmap, "scatter": _scatter, "waffle": _waffle,
              "tiles": _tiles, "panels": _panels, "quotes": _quotes, "episodes": _episodes, "code_card": _code_card,
              "dotplot": _dotplot, "histogram": _distribution("Histogram", "", default_unit=""),
              "box": _distribution("Box plot", None), "strip": _distribution("Strip plot", None, stat="mean"),
              "ecdf": _distribution("Cumulative distribution", "", default_unit=""),
              "violin": _distribution("Violin plot", None)}


def describe(kind: str, args: tuple, kw: dict) -> str | None:
    """Alt text for a chart call, or None when the chart has no describer (the title still serves)."""
    fn = DESCRIBERS.get(kind)
    if fn is None:
        return None
    try:
        return " ".join(fn(*args, **kw).split())
    except Exception:  # alt text must never break a figure
        return None
