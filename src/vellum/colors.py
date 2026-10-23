"""Color roles: name the conditions once per write-up, and every figure colors them the same way.

    vl.set_roles(baseline="Closed book", intervention="With search")
    vl.hbar({"Closed book": 59, "Longer prompt": 55, "With search": 12}, title=...)   # coral, gray, blue

baseline      coral   the condition without the intervention: the control, the untrained model, the bad outcome
intervention  blue    what the figure is about
second        sage    a second intervention that is also the point (use sparingly)
reference     dark    an outside reference that should still read clearly, such as chance or a published number
everything else       muted gray, so the intervention stands out

Roles apply to bar labels (one series) and to series names (grouped bars, lines, dumbbells). Explicit colors= still
win, and highlight= puts the accent on labels that have no role. A figure takes the roles in effect when it is made;
pass roles={"baseline": ..., "intervention": [...]} to one chart to add to them.
"""
from __future__ import annotations

import contextvars
from collections.abc import Mapping
from contextlib import contextmanager

ROLES = {"baseline": "coral", "intervention": "blue", "second": "sage", "reference": "dark"}
MUTED = "gray"

_global: dict[str, str] = {}  # label -> role
_active: contextvars.ContextVar[dict[str, str] | None] = contextvars.ContextVar("vellum_roles", default=None)
_logs: contextvars.ContextVar[tuple[list, ...]] = contextvars.ContextVar("vellum_color_logs", default=())


def _labels(v) -> list[str]:
    if v is None:
        return []
    if isinstance(v, str):
        return [v]
    return [str(x) for x in v]


def normalize(roles: Mapping | None) -> dict[str, str]:
    """{role: label or [labels]} -> {label: role}."""
    out: dict[str, str] = {}
    for role, labs in (roles or {}).items():
        if role not in ROLES:
            raise ValueError(f"unknown role {role!r}; use one of: {', '.join(ROLES)}")
        for lab in _labels(labs):
            out[lab] = role
    return out


def set_roles(*, baseline=None, intervention=None, second=None, reference=None) -> None:
    """Name the conditions once; every figure made afterwards colors them the same way. No arguments clears them."""
    _global.clear()
    _global.update(normalize({"baseline": baseline, "intervention": intervention, "second": second,
                              "reference": reference}))


def roles() -> dict[str, str]:
    """The roles in effect, as {label: role}."""
    cur = _active.get()
    return dict(_global if cur is None else cur)


def snapshot(extra: Mapping | None = None) -> dict[str, str]:
    """The global roles plus one figure's own {role: labels}, as {label: role}."""
    return {**_global, **normalize(extra)}


@contextmanager
def using(label_roles: dict[str, str] | None):
    """Make these {label: role} the roles in effect for the block (None keeps the current ones)."""
    token = _active.set(dict(label_roles)) if label_roles is not None else None
    try:
        yield
    finally:
        if token is not None:
            _active.reset(token)


def role_color(label: str) -> str | None:
    """The color of the label's role, or None when it has no role."""
    from . import theme as th
    r = roles().get(str(label))
    return th.color(ROLES[r]) if r else None


@contextmanager
def recording():
    """Collect the (label, color) pairs that charts assign while the block runs (nested blocks see them too)."""
    out: list[tuple[str, str]] = []
    token = _logs.set(_logs.get() + (out,))
    try:
        yield out
    finally:
        _logs.reset(token)


def note(labels, colors) -> None:
    """Called by the chart helpers for every label they color."""
    logs = _logs.get()
    if not logs or not labels:
        return
    pairs = [(str(lab), c) for lab, c in zip(labels, colors)]
    for log in logs:
        log.extend(pairs)


def card():
    """A figure of the color roles as everyone sees them: normal vision and the three color blindnesses."""
    from . import access
    from . import svg as S
    from . import theme as th
    from .figure import Body, Figure

    rows = [(role, name) for role, name in ROLES.items()] + [("everything else", MUTED)]
    cols = ["Normal vision", "Protanopia", "Deuteranopia", "Tritanopia"]
    LW, SW, SH, G, HEAD = 300, 120, 34, 10, 30

    def render(W: float) -> Body:
        out = []
        for j, c in enumerate(cols):
            out.append(S.text(LW + j * (SW + G) + SW / 2, 18, c, th.MIN_TEXT, th.MUTED, "middle"))
        for i, (role, name) in enumerate(rows):
            y = HEAD + i * (SH + G)
            hex_ = th.color(name)
            out.append(S.text(0, y + SH / 2 + 5, role, 15, th.INK, weight=600))
            out.append(S.text(150, y + SH / 2 + 5, f"{name}  {hex_}", 13, th.INK2))
            for j, kind in enumerate([None, *access.CVD]):
                out.append(S.rect(LW + j * (SW + G), y, SW, SH, hex_ if kind is None else access.simulate(hex_, kind), 6))
        return Body("".join(out), HEAD + len(rows) * (SH + G) - G)

    return Figure(render, title="Each color role stays distinct with every common color blindness", kind="palette",
                  meta={"alt": "Color roles: " + "; ".join(f"{r} {n} {th.color(n)}" for r, n in rows) + "."})
