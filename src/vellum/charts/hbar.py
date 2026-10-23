"""Horizontal bars: the workhorse of the clear style.

Labels on the left, square at the baseline, a 4px rounded data end, the value written at the tip,
light vertical gridlines and no axis lines. One accent on the point, the rest gray.
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
from .dist import attach_runs, dark, dots, run_values


def hbar(data, *, series=None, color=None, colors=None, highlight=None, accent="blue", sort=False,
         domain=None, ticks=None, step=None, unit=UNSET, decimals=None, fmt=None, signed=False,
         notes=None, ci=None, runs=None, ref=None, ref_label=None, values=True, axis=True, tick_format=None,
         row_height=None, bar_height=None, label_width=None,
         title=None, subtitle=None, legend=None, legend_position=None, frame=None, width=None) -> Figure:
    """Horizontal bar chart.

    data: {label: value}, {label: [v1, v2]} for grouped bars, a list of (label, value) pairs (may include
          vl.section("heading") rows), or a pandas Series / DataFrame.
    series: names of the grouped series (legend). colors: per series (grouped) or {label: color} (single).
    highlight: label(s) drawn in the accent color with a bold label; other bars go gray.
    notes: {label: "558 episodes"} muted text after the value. ci: {label: (lo, hi)} whiskers.
    runs: one dot per run or seed over its bar, the bar showing the value in data (usually the runs' mean):
    {label: [v, ...]}, or {label: [[series-1 runs], [series-2 runs]]} for grouped bars.
    ref: value of a reference line (e.g. the untrained model), ref_label: its label.
    unit: '%' by default; '' for plain numbers. decimals/fmt control value labels.
    """
    rows, ns, names = D.rows(data, series)
    names = list(series) if series is not None else names
    D.attach_ci(rows, ci, ns)
    runs_of = attach_runs(rows, runs, ns)
    unit, unit_given = resolve_unit(unit)
    if sort:
        if any(r.section for r in rows):
            raise ValueError("sort=True can't be combined with sections")
        rev = sort != "asc"
        rows.sort(key=lambda r: (r.values[0] is None, -(r.values[0] or 0) if rev else (r.values[0] or 0)))
    all_vals = [v for r in rows for v in r.values]
    SC.check_percent(all_vals, unit, unit_given)
    note_of = (notes if isinstance(notes, Mapping) else
               {r.label: n for r, n in zip([r for r in rows if not r.section], notes)} if notes else {})
    hl = as_set(highlight)

    def render(W: float) -> Body:
        data_rows = [r for r in rows if not r.section]
        nrows = len(data_rows)
        if ns == 1:
            if nrows <= 3:
                rh, bh, ls, vs, vw, vf = 54, 24, 14, 15, 600, th.INK
            elif nrows <= 8:
                rh, bh, ls, vs, vw, vf = 40, 20, 13.5, 14, 600, th.INK
            else:
                rh, bh, ls, vs, vw, vf = 25, 15, 12.5, 12, 400, th.INK2
            bgap = 0
        else:
            bh = 19 if ns <= 3 else 14
            bgap = 3
            rh = ns * bh + (ns - 1) * bgap + 20
            ls, vs, vw, vf = 13.5, 12.5, 600, th.INK
        rh = row_height or rh
        bh = bar_height or bh
        fmtv = SC.formatter(fmt, decimals, unit, signed, all_vals)

        # ---- domain
        ext = [v for v in all_vals if v is not None]
        for r in data_rows:
            for c in r.ci:
                if c:
                    ext += list(c)
        if ref is not None:
            ext.append(ref)
        ext += run_values(runs_of)
        if ticks is not None:
            lo, hi, tk = min(ticks), max(ticks), list(ticks)
        elif domain is not None:
            lo, hi, tk = SC.domain(ext, domain[0], domain[1], unit == "%", step=step)
        else:
            lo, hi, tk = SC.domain(ext, percent=unit == "%", step=step)
        tfmt = SC.tick_formatter(tk, unit, signed, tick_format)

        # ---- label column (wrap very long labels)
        def lab_style(r):
            return (ls + 1, 600, th.INK) if r.label in hl else (ls, 400, th.INK2)
        max_lab = label_width or 0.42 * W
        lab_lines = {}
        for r in data_rows:
            size, wt, _ = lab_style(r)
            lab_lines[r.label] = T.wrap_balanced(r.label, max_lab, size, "sans", wt) if T.width(r.label, size, "sans", wt) > max_lab else [r.label]
        L = max((max(T.width(ln, lab_style(r)[0], "sans", lab_style(r)[1]) for ln in lab_lines[r.label]) for r in data_rows), default=40) + 14
        if label_width:
            L = label_width + 14
        L = max(L, 0.24 * W)  # the originals kept a wide label column: short labels don't crowd the left edge

        # ---- right end: room for the longest value label and the last tick label
        R0 = min(W - (T.width(tfmt(hi), th.TICK_SIZE) / 2 + 2 if axis else 0), W - 0.1 * W)  # keep air on the right
        span = hi - lo
        rad = max(2.0, min(3.5, bh / 4))  # run dots
        for r in data_rows:
            rr = runs_of.get(id(r))
            for j, v in enumerate(r.values):
                if v is None or v <= 0 and lo < 0:
                    continue
                end = max(v, r.ci[j][1]) if r.ci and r.ci[j] else v
                if rr and rr[j]:
                    end = max(end, max(rr[j]))
                t = (end - lo) / span if span else 0
                if t <= 0:
                    continue
                lw = T.width(fmtv(v), vs, "sans", vw) if values else 0
                if rr and rr[j]:
                    lw += rad + 1
                note = note_of.get(r.label)
                if note and j == ns - 1:
                    lw += 7 + T.width(str(note), 12.5)
                R0 = min(R0, L + (W - 9 - lw - L) / t)
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
                lines = lab_lines[r.label]
                h = max(rh, len(lines) * lab_style(r)[0] * 1.25 + 8)
                layout.append((r, y, h))
                y += h
        bottom = y
        out = []
        if axis:
            for t in tk:
                out.append(S.line(x(t), top, x(t), bottom, th.GRID))
                out.append(S.text(x(t), bottom + 20, tfmt(t), th.TICK_SIZE, th.MUTED, "middle"))
        if ref is not None:
            out.append(S.line(x(ref), top, x(ref), bottom, th.INK2, 1.2))
            if ref_label:
                out.append(S.text(x(ref), top - 6, ref_label, th.TICK_SIZE, th.MUTED, "middle"))
        cols = series_colors(ns, colors if ns > 1 else None, names)
        single = row_colors([r.label for r in data_rows], color=color, colors=colors if ns == 1 else None,
                            highlight=highlight, accent=accent) if ns == 1 else None
        labels_svg = []
        k = 0
        for r, yy, h in layout:
            rr = runs_of.get(id(r))
            if r.section:
                out.append(S.text(0, yy + 24, r.label, 13, th.MUTED, weight=600))
                continue
            size, wt, fill = lab_style(r)
            lines = lab_lines[r.label]
            lh = size * 1.25
            first = yy + h / 2 - (len(lines) - 1) * lh / 2 + size * 0.36
            for i, ln in enumerate(lines):
                out.append(S.text(L - 14, first + i * lh, ln, size, fill, "end", wt))
            group_h = ns * bh + (ns - 1) * bgap
            for j, v in enumerate(r.values):
                rs = rr[j] if rr else []
                b = bh + (4 if (ns == 1 and r.label in hl and rh <= 40) else 0)
                by = yy + (h - group_h) / 2 + j * (bh + bgap) - (b - bh) / 2
                fillc = single[k] if ns == 1 else cols[j]
                if v is None:
                    if rs:
                        out.append(dots([x(u) for u in rs], by + b / 2, b / 2, rad, dark(fillc), True))
                    continue
                base = x(max(lo, min(0, hi))) if lo < 0 else x(lo)
                out.append(S.hbar(base, by, x(v), b, fillc))
                if rs:
                    out.append(dots([x(u) for u in rs], by + b / 2, b / 2, rad, dark(fillc), True))
                end_v = v
                c = r.ci[j] if r.ci else None
                if c:
                    cy = by + b / 2
                    cap = min(8, b * 0.55) / 2
                    out.append(S.line(x(c[0]), cy, x(c[1]), cy, th.INK, 1.2))
                    out.append(S.line(x(c[0]), cy - cap, x(c[0]), cy + cap, th.INK, 1.2))
                    out.append(S.line(x(c[1]), cy - cap, x(c[1]), cy + cap, th.INK, 1.2))
                    end_v = c[1] if v >= 0 else c[0]
                if values:
                    parts = [(fmtv(v), {"size": vs, "weight": vw, "fill": vf})]
                    note = note_of.get(r.label)
                    if note and j == ns - 1:
                        parts.append((str(note), {"size": 12.5, "fill": th.MUTED, "dx": 7}))
                    ty = by + b / 2 + vs * 0.36
                    halo = th.BG if ref is not None or c or rs else None
                    pos = v >= 0 or lo >= 0
                    lx = x(end_v) + 8 if pos else x(end_v) - 8
                    if rs:  # clear the outermost run dot
                        lx = max(lx, x(max(rs)) + rad + 9) if pos else min(lx, x(min(rs)) - rad - 9)
                    if pos:
                        labels_svg.append(S.spans(lx, ty, parts, halo=halo))
                    else:
                        labels_svg.append(S.spans(lx, ty, parts, anchor="end", halo=halo))
            k += 1
        out += labels_svg
        height = bottom + (30 if axis else 6)
        legend_items = [(nm, c) for nm, c in zip(names, cols)] if ns > 1 and names else None
        return Body("".join(out), height, legend_items)

    return Figure(render, title=title, subtitle=subtitle, legend=legend,
                  legend_position=legend_position, frame=frame, width=width, kind="hbar")
