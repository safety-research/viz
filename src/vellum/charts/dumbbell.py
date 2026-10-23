"""Dumbbell: two values per row joined by a line (before/after, without/with)."""
from __future__ import annotations

from .. import data as D
from .. import scale as SC
from .. import svg as S
from .. import text as T
from .. import theme as th
from ..figure import Body, Figure
from .common import UNSET, resolve_unit, series_colors


def dumbbell(data, *, series=("Without", "With"), colors=None, domain=None, ticks=None, step=None,
             unit=UNSET, decimals=None, fmt=None, sort=False, missing="doesn't apply", row_height=34,
             tick_format=None, title=None, subtitle=None, legend=None, legend_position=None,
             frame=None, width=None) -> Figure:
    """data: {label: (a, b)}; a uses the first color, b the second. None values print `missing`.
    sort: True sorts by the change b - a (largest first)."""
    rows, ns, _ = D.rows(data)
    if ns != 2:
        raise ValueError("dumbbell rows need two values: {label: (a, b)}")
    rows = [r for r in rows if not r.section]
    if sort:
        rows.sort(key=lambda r: -((r.values[1] or 0) - (r.values[0] or 0)) if None not in r.values else 1e9)
    unit, _ = resolve_unit(unit)
    vals = [v for r in rows for v in r.values if v is not None]
    cols = series_colors(2, None if colors is None else list(colors), list(series))

    def render(W: float) -> Body:
        if ticks is not None:
            lo, hi, tk = min(ticks), max(ticks), list(ticks)
        elif domain is not None:
            lo, hi, tk = SC.domain(vals, domain[0], domain[1], unit == "%", step=step)
        else:
            lo, hi, tk = SC.domain(vals, percent=unit == "%", zero=unit == "%", step=step)
        tfmt = SC.tick_formatter(tk, unit, False, tick_format)
        fmtv = SC.formatter(fmt, decimals, unit, False, vals)
        L = max(max((T.width(r.label, 13.5) for r in rows), default=40) + 14, 0.24 * W)
        R0 = W - max(T.width(fmtv(hi), 12) + 16, T.width(tfmt(hi), th.TICK_SIZE) / 2 + 2, 0.08 * W)
        x = lambda v: L + (R0 - L) * (v - lo) / (hi - lo)
        top = 4
        bottom = top + row_height * len(rows)
        out = []
        for t in tk:
            out.append(S.line(x(t), top, x(t), bottom, th.GRID))
            out.append(S.text(x(t), bottom + 20, tfmt(t), th.TICK_SIZE, th.MUTED, "middle"))
        for i, r in enumerate(rows):
            cy = top + row_height * (i + 0.5)
            out.append(S.text(L - 14, cy + 4.8, r.label, 13.5, th.INK2, "end"))
            a, b = r.values
            if a is None or b is None:
                out.append(S.text((L + R0) / 2, cy + 4.5, missing, 12, th.MUTED, "middle", italic=False))
                continue
            out.append(S.line(x(a), cy, x(b), cy, th.AXIS, 2))
            for v, c in ((a, cols[0]), (b, cols[1])):
                out.append(S.circle(x(v), cy, 6.5, c, th.BG, 1.5))
            left, right = (a, b) if a <= b else (b, a)
            out.append(S.text(x(left) - 11, cy + 4.3, fmtv(left), 12, th.INK2, "end"))
            out.append(S.text(x(right) + 11, cy + 4.3, fmtv(right), 12, th.INK2))
        return Body("".join(out), bottom + 30, list(zip(series, cols)), "round")

    return Figure(render, title=title, subtitle=subtitle, legend=legend,
                  legend_position=legend_position, frame=frame, width=width, kind="dumbbell")
