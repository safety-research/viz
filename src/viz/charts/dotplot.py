"""Dot plot: one dot per row on a shared axis, with an optional interval (a forest plot).

Labels on the left as in hbar, light vertical gridlines, the interval as a line in the dot's color and the value
written after it. Dots do not encode length, so the axis does not have to start at zero.
"""
from __future__ import annotations

from collections.abc import Mapping

from .. import data as D
from .. import scale as SC
from .. import svg as S
from .. import text as T
from .. import theme as th
from ..figure import Body, Figure
from .common import UNSET, as_set, resolve_unit, row_colors, series_colors


def dotplot(data, *, series=None, color=None, colors=None, highlight=None, accent="blue", sort=False,
            domain=None, ticks=None, step=None, zero=False, unit=UNSET, decimals=None, fmt=None, signed=False,
            tick_format=None, ci=None, ref=None, ref_label=None, notes=None, values=True, xlabel=None,
            row_height=None, dot_size=None, label_width=None,
            title=None, subtitle=None, legend=None, legend_position=None, frame=None, width=None) -> Figure:
    """Dot plot (forest plot): a dot per row, an optional horizontal interval, labels on the left.

    data: {label: value}, {label: [v1, v2]} with series=[...] for several dots per row (offset within the row),
          a list of (label, value) pairs (may include viz.section("heading") rows), or a pandas Series / DataFrame.
    ci: {label: (lo, hi)}, or {label: [(lo, hi), ...]} with series. ref: a reference line (0 for differences, 50 for
    no preference), ref_label its label. highlight: rows in the accent color with bold labels, the rest gray.
    notes: {label: "n = 400"} muted text after the value. xlabel: the measure, under the axis.
    unit: '%' by default (rates, differences in points); '' for scores and effect sizes. The axis includes zero
    only when zero=True or a value, interval or ref needs it.
    """
    rows, ns, names = D.rows(data, series)
    names = list(series) if series is not None else names
    D.attach_ci(rows, ci, ns)
    unit, unit_given = resolve_unit(unit)
    if sort:
        if any(r.section for r in rows):
            raise ValueError("sort=True can't be combined with sections")
        rev = sort != "asc"
        rows.sort(key=lambda r: (r.values[0] is None, -(r.values[0] or 0) if rev else (r.values[0] or 0)))
    all_vals = [v for r in rows for v in r.values]
    SC.check_percent(all_vals, unit, unit_given)
    data_rows = [r for r in rows if not r.section]
    note_of = (notes if isinstance(notes, Mapping) else
               {r.label: n for r, n in zip(data_rows, notes)} if notes else {})
    hl = as_set(highlight)

    def render(W: float) -> Body:
        nrows = len(data_rows)
        if ns == 1:
            rh, ls, vs, rad = ((46, 14, 13.5, 7) if nrows <= 3 else (36, 13.5, 13, 6.5) if nrows <= 10
                               else (28, 12.5, 12, 5.5))
            sub = 0.0
        else:
            rad = 5.5 if ns <= 3 else 4.5
            sub = 2 * rad + 5
            rh, ls, vs = (ns - 1) * sub + 2 * rad + 20, 13.5, 12.5
        rh = row_height or rh
        rad = dot_size or rad
        fmtv = SC.formatter(fmt, decimals, unit, signed, all_vals)

        def val_style(r):
            return (600, th.INK) if r.label in hl else (400, th.INK2)

        # ---- domain
        ext = [v for v in all_vals if v is not None]
        for r in data_rows:
            for c in r.ci:
                if c:
                    ext += list(c)
        if ref is not None:
            ext.append(ref)
        if ticks is not None:
            lo, hi, tk = min(ticks), max(ticks), list(ticks)
        elif domain is not None:
            lo, hi, tk = SC.domain(ext, domain[0], domain[1], unit == "%", step=step)
        else:
            lo, hi, tk = SC.domain(ext, percent=unit == "%", zero=zero, step=step)
        tfmt = SC.tick_formatter(tk, unit, signed, tick_format)
        span = (hi - lo) or 1.0

        # ---- label column, as in hbar
        def lab_style(r):
            return (ls + 1, 600, th.INK) if r.label in hl else (ls, 400, th.INK2)
        max_lab = label_width or 0.42 * W
        lab_lines = {}
        for r in data_rows:
            size, wt, _ = lab_style(r)
            wide = T.width(r.label, size, "sans", wt) > max_lab
            lab_lines[r.label] = T.wrap_balanced(r.label, max_lab, size, "sans", wt) if wide else [r.label]
        L = max((max(T.width(ln, lab_style(r)[0], "sans", lab_style(r)[1]) for ln in lab_lines[r.label])
                 for r in data_rows), default=40) + 14
        if label_width:
            L = label_width + 14
        L = max(L, 0.24 * W)

        # ---- right end: room for the value label after each interval and for the last tick label
        R0 = min(W - (T.width(tfmt(hi), th.TICK_SIZE) / 2 + 2), W - 0.08 * W)
        for r in data_rows:
            for j, v in enumerate(r.values):
                if v is None:
                    continue
                c = r.ci[j] if r.ci else None
                end = max(v, c[1]) if c else v
                t = (end - lo) / span
                if t <= 0:
                    continue
                lw = T.width(fmtv(v), vs, "sans", val_style(r)[0]) if values else 0
                note = note_of.get(r.label)
                if note and j == ns - 1:
                    lw += 7 + T.width(str(note), 12.5)
                R0 = min(R0, L + (W - 9 - rad - lw - L) / t)
        R0 = max(R0, L + 40)
        x = lambda v: L + (R0 - L) * (min(max(v, lo), hi) - lo) / span

        # ---- rows
        top = 18 if ref_label else 4
        y = top
        layout = []
        for r in rows:
            if r.section:
                layout.append((r, y, 32))
                y += 32
            else:
                h = max(rh, len(lab_lines[r.label]) * lab_style(r)[0] * 1.25 + 8)
                layout.append((r, y, h))
                y += h
        bottom = y
        out = []
        for t in tk:
            out.append(S.line(x(t), top, x(t), bottom, th.GRID))
            out.append(S.text(x(t), bottom + 20, tfmt(t), th.TICK_SIZE, th.MUTED, "middle"))
        if ref is not None:
            out.append(S.line(x(ref), top, x(ref), bottom, th.INK2, 1.2))
            if ref_label:
                out.append(S.text(x(ref), top - 6, ref_label, 12, th.MUTED, "middle"))
        cols = series_colors(ns, colors if ns > 1 else None, names)
        single = row_colors([r.label for r in data_rows], color=color, colors=colors if ns == 1 else None,
                            highlight=highlight, accent=accent) if ns == 1 else None
        def crosses_ref(a: float, b: float) -> bool:  # a label from a to b would touch the reference line
            return ref is not None and a - 6 < x(ref) < b + 6

        labels_svg = []
        k = 0
        for r, yy, h in layout:
            if r.section:
                out.append(S.text(0, yy + 24, r.label, 13, th.MUTED, weight=600))
                continue
            size, wt, fill = lab_style(r)
            lines = lab_lines[r.label]
            lh = size * 1.25
            first = yy + h / 2 - (len(lines) - 1) * lh / 2 + size * 0.36
            for i, ln in enumerate(lines):
                out.append(S.text(L - 14, first + i * lh, ln, size, fill, "end", wt))
            for j, v in enumerate(r.values):
                if v is None:
                    continue
                cy = yy + h / 2 + (j - (ns - 1) / 2) * sub
                col = single[k] if ns == 1 else cols[j]
                c = r.ci[j] if r.ci else None
                if c:
                    out.append(S.line(x(c[0]), cy, x(c[1]), cy, col, 2.2, cap="round"))
                out.append(S.circle(x(v), cy, rad, col, th.BG, 1.5))
                if values:
                    vw, vf = val_style(r)
                    parts = [(fmtv(v), {"size": vs, "weight": vw, "fill": vf})]
                    lw = T.width(fmtv(v), vs, "sans", vw)
                    note = note_of.get(r.label)
                    if note and j == ns - 1:
                        parts.append((str(note), {"size": 12.5, "fill": th.MUTED, "dx": 7}))
                        lw += 7 + T.width(str(note), 12.5)
                    lx, anchor = max(x(v) + rad, x(c[1]) if c else 0) + 8, "start"
                    if crosses_ref(lx, lx + lw):  # left of the interval instead, if that side is clear
                        left = min(x(v) - rad, x(c[0]) if c else x(v)) - 8
                        if left - lw >= L + 2 and not crosses_ref(left - lw, left):
                            lx, anchor = left, "end"
                    halo = th.BG if ref is not None else None
                    labels_svg.append(S.spans(lx, cy + vs * 0.36, parts, anchor=anchor, halo=halo))
            k += 1
        out += labels_svg
        height = bottom + 30
        if xlabel:
            out.append(S.text((L + R0) / 2, bottom + 46, xlabel, 12.5, th.INK2, "middle"))
            height += 24
        legend_items = [(nm, c) for nm, c in zip(names, cols)] if ns > 1 and names else None
        return Body("".join(out), height, legend_items, "round", meta={"plot_x": (L, R0)})

    return Figure(render, title=title, subtitle=subtitle, legend=legend,
                  legend_position=legend_position, frame=frame, width=width, kind="dotplot")
