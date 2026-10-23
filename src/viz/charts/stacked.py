"""Stacked horizontal bars: where the outcomes went (misbehaved / raised a concern / completed)."""
from __future__ import annotations

from .. import data as D
from .. import scale as SC
from .. import svg as S
from .. import text as T
from .. import theme as th
from ..figure import Body, Figure
from .common import UNSET, resolve_unit, series_colors


def stacked(data, *, series, colors=None, normalize=False, unit=UNSET, decimals=None, fmt=None, values=True,
            min_label_width=34, totals=False, axis=True, row_height=40, bar_height=24, sort=None,
            title=None, subtitle=None, legend=None, legend_position=None, frame=None,
            width=None) -> Figure:
    """data: {label: [v1, v2, ...]} in the order of `series`. normalize=True rescales each row to 100%.
    Segment values print inside segments wide enough to hold them. sort: a series name to sort rows by."""
    rows, ns, _ = D.rows(data, series)
    rows = [r for r in rows if not r.section]
    unit, _ = resolve_unit(unit)
    if normalize:
        for r in rows:
            t = sum(v or 0 for v in r.values) or 1
            r.values = [None if v is None else 100 * v / t for v in r.values]
    if sort is not None:
        j = list(series).index(sort)
        rows.sort(key=lambda r: -(r.values[j] or 0))
    cols = series_colors(ns, colors, list(series))
    sums = [sum(v or 0 for v in r.values) for r in rows]

    def render(W: float) -> Body:
        fmtv = SC.formatter(fmt, decimals, unit, False,
                            [v for r in rows for v in r.values])
        lo, hi, tk = SC.domain(sums + [0], percent=unit == "%")
        if normalize or (unit == "%" and max(sums) > 95):
            lo, hi, tk = 0.0, 100.0, [0, 25, 50, 75, 100]
        tfmt = SC.tick_formatter(tk, unit)
        L = max(max((T.width(r.label, 13.5) for r in rows), default=40) + 14, 0.24 * W)
        R0 = W - max(0.08 * W, (T.width(fmtv(max(sums)), 13, "sans", 600) + 14) if totals else 0,
                     T.width(tfmt(hi), th.TICK_SIZE) / 2 + 2)
        x = lambda v: L + (R0 - L) * (v - lo) / (hi - lo)
        top = 4
        bottom = top + row_height * len(rows)
        out = []
        if axis:
            for t in tk:
                out.append(S.line(x(t), top, x(t), bottom, th.GRID))
                out.append(S.text(x(t), bottom + 20, tfmt(t), th.TICK_SIZE, th.MUTED, "middle"))
        for i, r in enumerate(rows):
            y = top + row_height * i + (row_height - bar_height) / 2
            out.append(S.text(L - 14, y + bar_height / 2 + 4.8, r.label, 13.5, th.INK2, "end"))
            acc = 0.0
            segs = [(j, v) for j, v in enumerate(r.values) if v]
            for k, (j, v) in enumerate(segs):
                xa, xb = x(acc), x(acc + v)
                last = k == len(segs) - 1
                if last:
                    out.append(S.hbar(xa, y, xb, bar_height, cols[j]))
                else:
                    out.append(S.rect(xa, y, xb - xa + 0.4, bar_height, cols[j]))
                if values and xb - xa >= min_label_width:
                    out.append(S.text((xa + xb) / 2, y + bar_height / 2 + 4.3, fmtv(v), 12, th.text_on(cols[j]), "middle", 600))
                acc += v
            if totals:
                out.append(S.text(x(acc) + 8, y + bar_height / 2 + 4.8, fmtv(acc), 13, th.INK, weight=600))
        return Body("".join(out), bottom + (30 if axis else 6), list(zip(series, cols)))

    return Figure(render, title=title, subtitle=subtitle, legend=legend if legend is not None else True,
                  legend_position=legend_position, frame=frame, width=width, kind="stacked")
