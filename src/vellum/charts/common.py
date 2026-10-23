"""Helpers shared by the charts."""
from __future__ import annotations

from collections.abc import Mapping, Sequence

from .. import colors as roles
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


def series_colors(ns: int, colors=None, names: Sequence[str] | None = None, highlight=None) -> list[str]:
    """Colors for ns series: a list, a {series name: color} dict, else the color roles (vl.set_roles: named series
    get their role's color and the rest go gray), else the default order (coral, blue, sage, ...).
    highlight: series that keep their color; the others go gray."""
    names = list(names or [])
    gray = th.color(roles.MUTED)
    if colors is None:
        by_role = [roles.role_color(nm) for nm in names]
        if any(by_role):
            out = [c or gray for c in by_role] + [gray] * max(0, ns - len(by_role))
        elif ns == 1:
            out = [th.color("blue")]
        else:
            out = [th.color(c) for c in th.SERIES[:ns]] + [gray] * max(0, ns - len(th.SERIES))
    elif isinstance(colors, str):
        out = [th.color(colors)] * ns
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
        out = [c if nm in hl else gray for nm, c in zip(names, out)]
    if not isinstance(colors, str):  # one color for every series says nothing about any one of them
        roles.note(names, out)
    return out


def plot_height(factor: float = 1.0) -> float:
    """The body height axis charts share at the current figure size (vl.set_defaults(size=...))."""
    return th.current_size().plot * factor


def as_set(x) -> set[str]:
    if x is None:
        return set()
    if isinstance(x, str):
        return {x}
    return {str(v) for v in x}


def row_colors(labels: list[str], *, color=None, colors=None, highlight=None, accent: str = "blue") -> list[str]:
    """Per-bar colors for a single series: explicit per-label colors; else the label's color role (vl.set_roles);
    else the accent on highlighted rows; and when roles or a highlight are in play, gray for everything else.
    With none of these, a single color (blue)."""
    hl = as_set(highlight)
    by_role = [roles.role_color(lab) for lab in labels]
    muted = bool(hl) or any(by_role)
    out, own = [], []  # own: labels whose color is theirs (explicit, role, highlight), not a color all bars share
    for i, lab in enumerate(labels):
        if isinstance(colors, Mapping) and lab in colors:
            out.append(th.color(colors[lab]))
        elif isinstance(colors, Sequence) and not isinstance(colors, str) and i < len(colors):
            out.append(th.color(colors[i]))
        elif by_role[i]:
            out.append(by_role[i])
        elif lab in hl:
            out.append(th.color(accent))
        elif muted:
            out.append(th.color(color or roles.MUTED) if hl else th.color(roles.MUTED))
            continue
        else:
            out.append(th.color(color or "blue"))
            continue
        own.append(i)
    roles.note([labels[i] for i in own], [out[i] for i in own])
    return out
