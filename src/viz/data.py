"""Turn the shapes people actually pass (dicts, lists of pairs, pandas) into rows."""
from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field


@dataclass
class Section:
    """A group heading between rows of a horizontal bar chart: viz.section("Other values")."""
    label: str


def section(label: str) -> Section:
    return Section(label)


@dataclass
class Row:
    label: str
    values: list[float | None]
    section: bool = False
    ci: list[tuple[float, float] | None] = field(default_factory=list)


def _num(v) -> float | None:
    if v is None:
        return None
    try:
        f = float(v)
    except (TypeError, ValueError):
        raise TypeError(f"expected a number, got {v!r}") from None
    return None if math.isnan(f) else f


def _is_frame(obj) -> bool:
    return hasattr(obj, "columns") and hasattr(obj, "index") and hasattr(obj, "itertuples")


def _is_series(obj) -> bool:
    return hasattr(obj, "index") and hasattr(obj, "items") and not hasattr(obj, "columns")


def rows(data, series: Sequence[str] | None = None) -> tuple[list[Row], int, list[str] | None]:
    """Normalize chart data to rows. Returns (rows, number of series, series names from the data or None)."""
    names = None
    if _is_frame(data):
        names = [str(c) for c in data.columns]
        items = [(str(idx), [_num(v) for v in row]) for idx, *row in data.itertuples()]
    elif _is_series(data) or isinstance(data, Mapping):
        items = list(data.items())
    elif isinstance(data, Sequence) and not isinstance(data, str):
        items = list(data)
    else:
        raise TypeError("data should be a dict {label: value}, a list of (label, value) pairs, or a pandas object")
    out: list[Row] = []
    width = None
    for it in items:
        if isinstance(it, Section):
            out.append(Row(it.label, [], section=True))
            continue
        if isinstance(it, Mapping) and "section" in it:
            out.append(Row(str(it["section"]), [], section=True))
            continue
        label, val = it
        if isinstance(val, (list, tuple)) or (hasattr(val, "__len__") and not isinstance(val, str)):
            vals = [_num(v) for v in val]
        else:
            vals = [_num(val)]
        if width is None:
            width = len(vals)
        elif len(vals) != width:
            raise ValueError(f"row {label!r} has {len(vals)} values, earlier rows have {width}")
        out.append(Row(str(label), vals))
    ns = width or 1
    if series is not None and len(series) != ns:
        raise ValueError(f"{len(series)} series names for {ns} values per row")
    return out, ns, names


def attach_ci(rs: list[Row], ci, ns: int) -> None:
    """ci: {label: (lo, hi)} for one series, {label: [(lo, hi), ...]} for several, or a list aligned with rows."""
    if ci is None:
        return
    data_rows = [r for r in rs if not r.section]
    if isinstance(ci, Mapping):
        get = lambda r: ci.get(r.label)
    else:
        seq = list(ci)
        if len(seq) != len(data_rows):
            raise ValueError(f"ci has {len(seq)} entries for {len(data_rows)} rows")
        lookup = {id(r): c for r, c in zip(data_rows, seq)}
        get = lambda r: lookup[id(r)]
    for r in data_rows:
        c = get(r)
        if c is None:
            r.ci = [None] * ns
        elif ns == 1 and len(c) == 2 and not isinstance(c[0], (list, tuple)):
            r.ci = [(float(c[0]), float(c[1]))]
        else:
            r.ci = [None if x is None else (float(x[0]), float(x[1])) for x in c]


def pairs(data) -> list[tuple[str, float]]:
    """{label: value} or [(label, value)] -> list of pairs (used by waffle, heatmap rows...)."""
    if _is_series(data) or isinstance(data, Mapping):
        return [(str(k), float(v)) for k, v in data.items()]
    return [(str(k), float(v)) for k, v in data]
