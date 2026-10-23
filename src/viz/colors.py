"""Color roles: name the conditions once per write-up, and every figure colors them the same way.

    viz.set_roles(control="Closed book", intervention="With search", second="Rerank")
    viz.hbar({"Closed book": 59, "Rerank": 30, "Longer prompt": 55, "With search": 12}, title=...)

control       light gray  the condition without the intervention: the baseline, the untrained model ("baseline"
                          means the same role)
intervention  orange      what the figure is about
second        blue        a second intervention
third         sage        a third
fourth        purple      a fourth (for red-green color-blind readers it nears blue, so label it)
fifth         ochre       a fifth (it nears orange the same way)
ordered       light blue to navy, for conditions with an order: doses, model sizes, training steps
everything else           muted gray, so the named conditions stand out (muted series take three shades in turn)

A reference such as chance or the base model is a dashed line (ref=), not a color.

Roles apply to bar labels (one series) and to series names (grouped bars, lines, dumbbells). Explicit colors= still
win; with roles in play, highlight= only bolds a label. A figure takes the roles in effect when it is made; pass
roles={"control": ..., "intervention": [...]} to one chart to add to them. A viz-roles.json file in the working
folder or any folder above it, {"control": "Closed book", "intervention": ["With search"]}, sets the roles for every
script and agent working on that write-up; viz.set_roles replaces it for one script.
"""
from __future__ import annotations

import contextvars
import json
from collections.abc import Mapping
from contextlib import contextmanager
from pathlib import Path

ROLES = {"control": "gray", "intervention": "coral", "second": "blue", "third": "sage", "fourth": "plum",
         "fifth": "ochre"}
ALIASES = {"baseline": "control"}
ROLE_NAMES = (*ROLES, *ALIASES, "ordered")
MUTED = "gray"
ROLES_FILE = "viz-roles.json"

_global: dict[str, str] = {}  # label -> role ("ordered:i/n" for ordered conditions)
_state = {"loaded": False, "source": None}  # whether a roles file was looked for, and the one found
_active: contextvars.ContextVar[dict[str, str] | None] = contextvars.ContextVar("viz_roles", default=None)
_logs: contextvars.ContextVar[tuple[list, ...]] = contextvars.ContextVar("viz_color_logs", default=())


def _labels(v) -> list[str]:
    if v is None:
        return []
    if isinstance(v, str):
        return [v]
    return [str(x) for x in v]


def normalize(roles: Mapping | None) -> dict[str, str]:
    """{role: label or [labels]} -> {label: role}; ordered labels become "ordered:i/n"."""
    out: dict[str, str] = {}
    for role, labs in (roles or {}).items():
        if role not in ROLE_NAMES:
            raise ValueError(f"unknown role {role!r}; use one of: {', '.join(ROLE_NAMES)}")
        labs = _labels(labs)
        for i, lab in enumerate(labs):
            out[lab] = f"ordered:{i}/{len(labs)}" if role == "ordered" else ALIASES.get(role, role)
    return out


def find_roles_file(start: str | Path | None = None) -> Path | None:
    """The nearest viz-roles.json in this folder or above it."""
    here = Path(start or Path.cwd()).resolve()
    for d in (here, *here.parents):
        f = d / ROLES_FILE
        if f.is_file():
            return f
    return None


def load_roles(path: str | Path) -> None:
    """Take the roles from a JSON file: {"baseline": ..., "intervention": [...], "ordered": [...]}."""
    p = Path(path)
    _global.clear()
    _global.update(normalize(json.loads(p.read_text())))
    _state.update(loaded=True, source=p.resolve())


def _ensure() -> None:
    if not _state["loaded"]:
        _state["loaded"] = True
        f = find_roles_file()
        if f is not None:
            load_roles(f)


def source() -> Path | None:
    """The roles file in effect, or None when the roles come from code (or there are none)."""
    _ensure()
    return _state["source"]


def set_roles(*, control=None, intervention=None, second=None, third=None, fourth=None, fifth=None, ordered=None,
              baseline=None) -> None:
    """Name the conditions once; every figure made afterwards colors them the same way. Replaces a roles file;
    no arguments clears the roles. baseline= is another name for control=."""
    _state.update(loaded=True, source=None)
    _global.clear()
    _global.update(normalize({"control": control, "baseline": baseline, "intervention": intervention,
                              "second": second, "third": third, "fourth": fourth, "fifth": fifth,
                              "ordered": ordered}))


def roles() -> dict[str, str]:
    """The roles in effect, as {label: role}."""
    _ensure()
    cur = _active.get()
    return dict(_global if cur is None else cur)


def snapshot(extra: Mapping | None = None) -> dict[str, str]:
    """The global roles plus one figure's own {role: labels}, as {label: role}."""
    _ensure()
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
    if not r:
        return None
    if r.startswith("ordered:"):
        i, n = (int(x) for x in r.split(":", 1)[1].split("/"))
        return th.ramp(n)[i]
    return th.color(ROLES[r])


@contextmanager
def recording():
    """Collect the (label, color) pairs that charts assign while the block runs (nested blocks see them too)."""
    out: list[tuple[str, str]] = []
    token = _logs.set(_logs.get() + (out,))
    try:
        yield out
    finally:
        _logs.reset(token)


def note(labels, colors, specific: bool = True) -> None:
    """Called by the chart helpers for every label they color. specific=False marks a color the label didn't choose
    (muted for having no role, or one color shared by every bar), which the consistency check ignores."""
    logs = _logs.get()
    if not logs or not labels:
        return
    entries = [(str(lab), c, specific) for lab, c in zip(labels, colors)]
    for log in logs:
        log.extend(entries)


def card():
    """A figure of the color roles as everyone sees them: normal vision and the three color blindnesses."""
    from . import access
    from . import svg as S
    from . import theme as th
    from .figure import Body, Figure

    shown = {"plum": "purple", "coral": "orange", "gray": "light gray"}
    rows = [(role, shown.get(name, name), [th.color(name)]) for role, name in ROLES.items()]
    rows += [("ordered", "light blue to navy", th.ramp(4)),
             ("everything else", "gray shades", [th.color(c) for c in th.MUTED_SHADES])]
    cols = ["Normal vision", "Protanopia", "Deuteranopia", "Tritanopia"]
    LW, SW, SH, G, HEAD = 330, 120, 34, 10, 30

    def render(W: float) -> Body:
        out = []
        for j, c in enumerate(cols):
            out.append(S.text(LW + j * (SW + G) + SW / 2, 18, c, th.MIN_TEXT, th.MUTED, "middle"))
        for i, (role, desc, hexes) in enumerate(rows):
            y = HEAD + i * (SH + G)
            out.append(S.text(0, y + SH / 2 + 5, role, 15, th.INK, weight=600))
            out.append(S.text(150, y + SH / 2 + 5, desc, 13, th.INK2))
            for j, kind in enumerate([None, *access.CVD]):
                x0, w = LW + j * (SW + G), SW / len(hexes)
                for k, h in enumerate(hexes):
                    fill = h if kind is None else access.simulate(h, kind)
                    out.append(S.rect(x0 + k * w, y, w + (0.5 if k < len(hexes) - 1 else 0), SH, fill))
        return Body("".join(out), HEAD + len(rows) * (SH + G) - G)

    return Figure(render, title="The control and first three colors stay distinct for color-blind readers", kind="palette",
                  meta={"alt": "Color roles: " + "; ".join(f"{r}: {d}" for r, d, _ in rows) + "."})
