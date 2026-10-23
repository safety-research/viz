"""Vertical bars: the look copied from the Anthropic-blog reference mockups.

Square bars, coral next to blue, the value above each bar, left and bottom axis lines, a rotated
y title, category labels wrapped under each group, whiskers for intervals, a dashed reference line.
"""
from __future__ import annotations

from .. import data as D
from .. import scale as SC
from .. import svg as S
from .. import text as T
from .. import theme as th
from ..figure import Body, Figure
from .common import UNSET, plot_height, resolve_unit, row_colors, series_colors


def bars(data, *, series=None, color=None, colors=None, highlight=None, accent="blue",
         domain=None, ticks=None, step=None, unit=UNSET, decimals=None, fmt=None, signed=False, tick_format=None,
         ci=None, ref=None, ref_label=None, ylabel=None, height=None, values=True, value_labels="all", grid=False,
         bar_width=None, title=None, subtitle=None, legend=None, legend_position=None, frame=None,
         width=None) -> Figure:
    """Vertical (grouped) bar chart.

    data: {label: value}, {label: [v1, v2]}, list of pairs, or pandas. series: names for grouped bars.
    colors: per series (grouped) or {label: color} / list per bar (one series). highlight: accent on some bars.
    ci: {label: (lo, hi)} or {label: [(lo, hi), ...]}. ref: dashed reference line (e.g. 50 for no preference).
    ylabel: rotated axis title. value_labels: "all", "first" (only the first series) or "none".
    """
    rows, ns, names = D.rows(data, series)
    names = list(series) if series is not None else names
    D.attach_ci(rows, ci, ns)
    rows = [r for r in rows if not r.section]
    unit, unit_given = resolve_unit(unit)
    all_vals = [v for r in rows for v in r.values]
    SC.check_percent(all_vals, unit, unit_given)

    fig = Figure(None, title=title, subtitle=subtitle, legend=legend,
                 legend_position=legend_position, frame=frame, width=width, kind="bars")

    def render(W: float) -> Body:
        n = len(rows)
        compact = W < 520
        m_l, m_r, m_t = (48 if compact else 58), 10, 22
        pw = W - m_l - m_r
        gw = pw / max(n, 1)
        cat = th.MIN_TEXT
        lines = [T.wrap(r.label, gw - 8, cat) for r in rows]
        max_lines = max((len(x) for x in lines), default=1)
        max_lines = max(max_lines, fig.meta.get("cat_lines", 0))  # panels in one row share a label depth
        m_b = 14 + max_lines * 14
        H = height or plot_height()
        ph = H - m_t - m_b
        ext = [v for v in all_vals if v is not None]
        for r in rows:
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
            lo, hi, tk = SC.domain(ext, percent=unit == "%", step=step, full_percent_step=25 if compact else 20)
        tfmt = SC.tick_formatter(tk, unit, signed, tick_format)
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
            out.append(S.rotated(12 if compact else 14, m_t + ph / 2, ylabel, size=th.MIN_TEXT))
        cols = series_colors(ns, colors if ns > 1 else None, names)
        single = row_colors([r.label for r in rows], color=color, colors=colors if ns == 1 else None,
                            highlight=highlight, accent=accent) if ns == 1 else None
        for i, r in enumerate(rows):
            cx = m_l + gw * (i + 0.5)
            total = ns * bw + (ns - 1) * gap
            for j, v in enumerate(r.values):
                if v is None:
                    continue
                x = cx - total / 2 + j * (bw + gap)
                fill = single[i] if ns == 1 else cols[j]
                y0, y1 = y(base_v), y(v)
                if abs(y1 - y0) < 1.5 and v != base_v:
                    y1 = y0 - 1.5 if v > base_v else y0 + 1.5
                out.append(S.vbar(x, y0, y1, bw, fill))
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
                    ly = ((y(c[0]) if c else y1) + 13) if neg else ((y(c[1]) if c else y1) - 5)
                    out.append(S.text(xc, ly, fmtv(v), th.MIN_TEXT, th.INK2, "middle"))
            for k, ln in enumerate(lines[i]):
                out.append(S.text(cx, m_t + ph + 18 + k * 14, ln, cat, th.INK2, "middle"))
        legend_items = [(nm, c) for nm, c in zip(names, cols)] if ns > 1 and names else None
        # plot_x: where the bars live, so a panel container can center its title over the plot, not the tick margin
        return Body("".join(out), H, legend_items, meta={"cat_lines": max_lines, "plot_x": (m_l, W - m_r)})

    fig.render = render
    return fig
