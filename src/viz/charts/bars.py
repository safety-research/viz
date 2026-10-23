"""Vertical bars.

Square bars, the baseline next to the intervention, the value above each bar, left and bottom axis lines, a rotated
y title, category labels wrapped under each group, whiskers for intervals, a dashed reference line.
"""
from __future__ import annotations

from .. import data as D
from .. import scale as SC
from .. import svg as S
from .. import text as T
from .. import theme as th
from ..figure import Body, Figure
from .common import UNSET, YLABEL_BAND, YLABEL_X, as_set, plot_height, resolve_unit, row_colors, series_colors, sort_key
from .dist import attach_runs, dark, dots, run_values


def bars(data, *, series=None, color=None, colors=None, highlight=None, accent="intervention", sort=None,
         domain=None, ticks=None, step=None, unit=UNSET, decimals=None, fmt=None, signed=False, tick_format=None,
         ci=None, runs=None, ref=None, ref_label=None, ylabel=None, height=None, values=True, value_labels="all", grid=False,
         bar_width=None, title=None, subtitle=None, legend=None, legend_position=None, width=None) -> Figure:
    """Vertical (grouped) bar chart.

    data: {label: value}, {label: [v1, v2]}, list of pairs, or pandas. series: names for grouped bars.
    colors: per series (grouped) or {label: color} / list per bar (one series). highlight: accent on some bars.
    ci: {label: (lo, hi)} or {label: [(lo, hi), ...]}. ref: dashed reference line (e.g. 50 for no preference).
    runs: one dot per run or seed over its bar, the bar showing the value in data (usually the runs' mean):
    {label: [v, ...]}, or {label: [[series-1 runs], [series-2 runs]]} for grouped bars.
    ylabel: rotated axis title. value_labels: "all", "first" (only the first series) or "none".
    sort: True puts the largest bar first, "asc" the smallest; grouped bars sort by the intervention's value, else
    their mean. Leave it out to keep the given order (the checks warn when categories are out of value order).
    """
    rows, ns, names = D.rows(data, series)
    names = list(series) if series is not None else names
    D.attach_ci(rows, ci, ns)
    rows = [r for r in rows if not r.section]
    runs_of = attach_runs(rows, runs, ns)
    if sort:
        key = {id(r): sort_key(r.values, names) for r in rows}
        rows.sort(key=lambda r: (key[id(r)] is None, -(key[id(r)] or 0) if sort != "asc" else (key[id(r)] or 0)))
    unit, unit_given = resolve_unit(unit)
    all_vals = [v for r in rows for v in r.values]
    SC.check_percent(all_vals, unit, unit_given)

    fig = Figure(None, title=title, subtitle=subtitle, legend=legend,
                 legend_position=legend_position, width=width, kind="bars")

    def render(W: float) -> Body:
        n = len(rows)
        compact = W < 520
        ext = [v for v in all_vals if v is not None]
        for r in rows:
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
            lo, hi, tk = SC.domain(ext, percent=unit == "%", step=step, full_percent_step=25 if compact else 20)
        tfmt = SC.tick_formatter(tk, unit, signed, tick_format)
        tw = max((T.width(tfmt(t), th.TICK_SIZE) for t in tk), default=0.0)
        m_l = max(48 if compact else 58, tw + 13 + (YLABEL_BAND if ylabel else 0))  # ticks end 9 px left of the axis
        m_r, m_t = 10, 22
        pw = W - m_l - m_r
        gw = pw / max(n, 1)
        cat = th.MIN_TEXT
        lines = [T.wrap(r.label, gw - 8, cat) for r in rows]
        max_lines = max((len(x) for x in lines), default=1)
        max_lines = max(max_lines, fig.meta.get("cat_lines", 0))  # panels in one row share a label depth
        m_b = 14 + max_lines * 14
        H = height or plot_height()
        ph = H - m_t - m_b
        fmtv = SC.formatter(fmt, decimals, unit, signed, all_vals)
        y = lambda v: m_t + ph * (1 - (min(max(v, lo), hi) - lo) / (hi - lo))
        base_v = max(lo, 0)
        cap = (22 if ns > 2 else 34 if ns == 2 else 46) * (1.5 if n <= 3 and not compact else 1)
        bw = bar_width or min(cap, gw * (0.25 if ns > 2 else 0.36 if ns == 2 else 0.5))
        gap = 3
        out = []
        for t in tk:
            if grid and t > lo:
                out.append(S.line(m_l, y(t), W - m_r, y(t), th.GRID))
            out.append(S.text(m_l - 9, y(t) + 4, tfmt(t), th.TICK_SIZE, th.MUTED, "end"))
        out.append(S.line(m_l, m_t - 4, m_l, m_t + ph, th.AXIS))
        out.append(S.line(m_l, m_t + ph, W - m_r, m_t + ph, th.AXIS))
        if lo < 0:
            out.append(S.line(m_l, y(0), W - m_r, y(0), th.MUTED))
        if ref is not None:
            out.append(S.line(m_l, y(ref), W - m_r, y(ref), th.MUTED, 1, "4 4"))
            if ref_label:
                out.append(S.text(W - m_r, y(ref) - 6, ref_label, th.MIN_TEXT, th.MUTED, "end"))
        if ylabel:
            out.append(S.rotated(YLABEL_X, m_t + ph / 2, ylabel, size=th.MIN_TEXT))
        cols = series_colors(ns, colors if ns > 1 else None, names)
        single = row_colors([r.label for r in rows], color=color, colors=colors if ns == 1 else None,
                            highlight=highlight, accent=accent) if ns == 1 else None
        rad = max(2.0, min(4.0, bw / 5))  # run dots
        for i, r in enumerate(rows):
            cx = m_l + gw * (i + 0.5)
            total = ns * bw + (ns - 1) * gap
            rr = runs_of.get(id(r))
            for j, v in enumerate(r.values):
                x = cx - total / 2 + j * (bw + gap)
                fill = single[i] if ns == 1 else cols[j]
                rs = rr[j] if rr else []
                if v is None:
                    if rs:
                        out.append(dots([y(u) for u in rs], x + bw / 2, bw / 2, rad, dark(fill), False))
                    continue
                y0, y1 = y(base_v), y(v)
                if abs(y1 - y0) < 1.5 and v != base_v:
                    y1 = y0 - 1.5 if v > base_v else y0 + 1.5
                out.append(S.vbar(x, y0, y1, bw, fill))
                if rs:
                    out.append(dots([y(u) for u in rs], x + bw / 2, bw / 2, rad, dark(fill), False))
                c = r.ci[j] if r.ci else None
                xc = x + bw / 2
                if c and c[1] - c[0] > 1e-9:
                    ya, yb = y(c[0]), y(c[1])
                    cap = min(4, bw / 3)
                    out.append(S.line(xc, ya, xc, yb, th.INK, 1.2))
                    out.append(S.line(xc - cap, ya, xc + cap, ya, th.INK, 1.2))
                    out.append(S.line(xc - cap, yb, xc + cap, yb, th.INK, 1.2))
                if values and value_labels != "none" and not (value_labels == "first" and j > 0):
                    neg = v < base_v
                    edge = (y(c[0]) if c else y1) if neg else (y(c[1]) if c else y1)
                    if rs:  # clear the lowest or highest run dot
                        edge = max(edge, y(min(rs)) + rad + 1) if neg else min(edge, y(max(rs)) - rad - 1)
                    ly = (edge + 13) if neg else (edge - 5)
                    out.append(S.text(xc, ly, fmtv(v), th.MIN_TEXT, th.INK2, "middle"))
            strong = r.label in as_set(highlight)  # the bar you are pointing at: a bold label
            for k, ln in enumerate(lines[i]):
                out.append(S.text(cx, m_t + ph + 18 + k * 14, ln, cat, th.INK if strong else th.INK2, "middle",
                                  600 if strong else 400))
        legend_items = [(nm, c) for nm, c in zip(names, cols)] if ns > 1 and names else None
        # plot_x: where the bars live, so a panel container can center its title over the plot, not the tick margin
        return Body("".join(out), H, legend_items, meta={"cat_lines": max_lines, "plot_x": (m_l, W - m_r)})

    fig.render = render
    return fig
