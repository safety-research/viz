"""Helpers shared by the charts."""
from __future__ import annotations

import re
from collections.abc import Mapping, Sequence

from .. import colors as roles
from .. import theme as th


class _Unset:
    def __repr__(self):
        return "UNSET"


UNSET = _Unset()


ACCENT = "intervention"  # a chart's one color when nothing else sets it: the intervention role's orange


def resolve_unit(unit) -> tuple[str, bool]:
    """Percent is the default unit; returns (unit, whether the caller set it)."""
    if unit is UNSET:
        return "%", False
    return ("" if unit is None else str(unit)), True


def _muted(k: int) -> str:
    """The k-th muted series color: gray, gray-light, gray-dark, then again."""
    return th.color(th.MUTED_SHADES[k % len(th.MUTED_SHADES)])


def series_colors(ns: int, colors=None, names: Sequence[str] | None = None, highlight=None) -> list[str]:
    """Colors for ns series: a list, a {series name: color} dict, else the color roles (viz.set_roles: named series
    get their role's color and the rest take the muted shades in turn), else the default order (orange, blue, sage,
    ...; one series alone is orange). highlight: series that keep their color; the others go gray."""
    names = list(names or [])
    gray = th.color(roles.MUTED)
    specific = [True] * ns
    if colors is None:
        by_role = [roles.role_color(nm) for nm in names] + [None] * max(0, ns - len(names))
        if any(by_role):
            out, k = [], 0
            for i, c in enumerate(by_role[:ns]):
                if c:
                    out.append(c)
                else:
                    out.append(_muted(k))
                    specific[i] = False
                    k += 1
        elif ns == 1:
            out = [th.color(ACCENT)]
        else:
            out = [th.color(c) for c in th.SERIES[:ns]] + [_muted(k) for k in range(max(0, ns - len(th.SERIES)))]
    elif isinstance(colors, str):
        out = [th.color(colors)] * ns
        specific = [False] * ns  # one color for every series says nothing about any one of them
    elif isinstance(colors, Mapping):
        if not names:
            raise ValueError("a {series: color} mapping needs series names")
        out = [th.color(colors[nm]) if nm in colors else (roles.role_color(nm) or th.color(th.SERIES[i % len(th.SERIES)]))
               for i, nm in enumerate(names)]
    else:
        cs = [th.color(c) for c in colors]
        if len(cs) < ns:
            raise ValueError(f"{len(cs)} colors for {ns} series")
        out = cs[:ns]
    hl = as_set(highlight)
    if hl:
        specific = [sp and nm in hl for nm, sp in zip(names, specific)]
        out = [c if nm in hl else gray for nm, c in zip(names, out)]
    roles.note([n for n, sp in zip(names, specific) if sp], [c for c, sp in zip(out, specific) if sp])
    roles.note([n for n, sp in zip(names, specific) if not sp], [c for c, sp in zip(out, specific) if not sp], False)
    return out


_MODEL = re.compile(r"\b(models?|gpt|claude|opus|sonnet|haiku|llama|qwen|gemma|gemini|mistral|mixtral|olmo|deepseek|"
                    r"phi|grok|base|instruct|chat)\b|\d+(\.\d+)?\s?[bBmM]\b|-\d+[bB]\b", re.I)


def looks_like_models(labels: Sequence[str]) -> bool:
    """Rows that name models (Model A, Qwen3-8B, Claude Opus...): their order usually means something."""
    labs = [str(x) for x in labels if x]
    return bool(labs) and sum(bool(_MODEL.search(x)) for x in labs) * 2 >= len(labs)


def sort_key(values: Sequence[float | None], names: Sequence[str] | None = None) -> float | None:
    """What a row is sorted by: its value, or for grouped rows the intervention's value, else their mean."""
    vals = list(values)
    if len(vals) == 1:
        return vals[0]
    rl = roles.roles()
    for nm, v in zip(names or [], vals):
        if rl.get(str(nm)) == "intervention":
            return v
    have = [v for v in vals if v is not None]
    return sum(have) / len(have) if have else None


def plot_height(factor: float = 1.0) -> float:
    """The body height axis charts share at the current figure size (viz.set_defaults(size=...))."""
    return th.current_size().plot * factor


def as_set(x) -> set[str]:
    if x is None:
        return set()
    if isinstance(x, str):
        return {x}
    return {str(v) for v in x}


def row_colors(labels: list[str], *, color=None, colors=None, highlight=None, accent: str = ACCENT) -> list[str]:
    """Per-bar colors for a single series: explicit per-label colors; else the label's color role (viz.set_roles),
    with every label that has no role muted (highlight= then only bolds a label, it doesn't recolor it); else the
    accent on highlighted rows and gray for the rest; else a single color (the accent, orange)."""
    hl = as_set(highlight)
    by_role = [roles.role_color(lab) for lab in labels]
    in_play = any(by_role)
    out, own = [], []  # own: labels whose color is theirs (explicit, role, highlight), not one every bar shares
    for i, lab in enumerate(labels):
        if isinstance(colors, Mapping) and lab in colors:
            out.append(th.color(colors[lab]))
        elif isinstance(colors, Sequence) and not isinstance(colors, str) and i < len(colors):
            out.append(th.color(colors[i]))
        elif by_role[i]:
            out.append(by_role[i])
        elif in_play:
            out.append(th.color(roles.MUTED))
            continue
        elif lab in hl:
            out.append(th.color(accent))
        elif hl:
            out.append(th.color(color or roles.MUTED))
            continue
        else:
            out.append(th.color(color or ACCENT))
            continue
        own.append(i)
    rest = [i for i in range(len(labels)) if i not in own]
    roles.note([labels[i] for i in own], [out[i] for i in own])
    roles.note([labels[i] for i in rest], [out[i] for i in rest], False)
    return out
