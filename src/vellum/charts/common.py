"""Helpers shared by the charts."""
from __future__ import annotations

from collections.abc import Mapping, Sequence

from .. import theme as th


class _Unset:
    def __repr__(self):
        return "UNSET"


UNSET = _Unset()


def resolve_unit(unit) -> tuple[str, bool]:
    """Percent is the default unit; returns (unit, whether the caller set it)."""
    if unit is UNSET:
        return "%", False
    return ("" if unit is None else str(unit)), True


def series_colors(ns: int, colors=None, names: Sequence[str] | None = None) -> list[str]:
    """Colors for ns series: a list, a {series name: color} dict, or the default order (coral, blue, sage, ...)."""
    if colors is None:
        if ns == 1:
            return [th.color("blue")]
        return [th.color(c) for c in th.SERIES[:ns]] + [th.color("gray")] * max(0, ns - len(th.SERIES))
    if isinstance(colors, str):
        return [th.color(colors)] * ns
    if isinstance(colors, Mapping):
        if not names:
            raise ValueError("a {series: color} mapping needs series names")
        return [th.color(colors.get(nm, th.SERIES[i % len(th.SERIES)])) for i, nm in enumerate(names)]
    cs = [th.color(c) for c in colors]
    if len(cs) < ns:
        raise ValueError(f"{len(cs)} colors for {ns} series")
    return cs[:ns]


def as_set(x) -> set[str]:
    if x is None:
        return set()
    if isinstance(x, str):
        return {x}
    return {str(v) for v in x}


def row_colors(labels: list[str], *, color=None, colors=None, highlight=None, accent: str = "blue") -> list[str]:
    """Per-bar colors for a single series: explicit per-label colors, else one accent on the highlighted rows
    (everything else gray), else a single color (blue)."""
    hl = as_set(highlight)
    out = []
    for i, lab in enumerate(labels):
        if isinstance(colors, Mapping) and lab in colors:
            out.append(th.color(colors[lab]))
        elif isinstance(colors, Sequence) and not isinstance(colors, str) and i < len(colors):
            out.append(th.color(colors[i]))
        elif hl:
            out.append(th.color(accent) if lab in hl else th.color(color or "gray"))
        else:
            out.append(th.color(color or "blue"))
    return out
