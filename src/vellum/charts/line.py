"""Lines over steps or doses, labeled at their ends instead of with a legend box."""
from __future__ import annotations

import math
from collections.abc import Mapping

from .. import scale as SC
from .. import svg as S
from .. import text as T
from .. import theme as th
from ..figure import Body, Figure
from .common import UNSET, as_set, plot_height, resolve_unit, series_colors


def _series(series, x):
    out = {}
    for name, ys in series.items():
        if isinstance(ys, Mapping):
            pts = [(float(k), None if v is None else float(v)) for k, v in ys.items()]
        else:
            ys = list(ys)
            if ys and isinstance(ys[0], (list, tuple)):
                pts = [(float(a), None if b is None else float(b)) for a, b in ys]
            else:
                if x is None:
                    xs = list(range(len(ys)))
                else:
                    xs = list(x)
                    if len(xs) != len(ys):
                        raise ValueError(f"series {name!r} has {len(ys)} values for {len(xs)} x positions")
                pts = [(float(a), None if b is None else float(b)) for a, b in zip(xs, ys)]
        out[str(name)] = pts
    return out


def line(series, *, x=None, colors=None, highlight=None, domain=None, ticks=None, step=None, xticks=None,
         xtick_labels=None, unit=UNSET, xunit="", decimals=None, fmt=None, xlabel=None, ylabel=None, bands=None,
         markers=True, end_labels=True, end_values=True, ref=None, ref_label=None, height=None, zero=True, xscale="linear",
         title=None, subtitle=None, legend=False, legend_position=None, frame=None, width=None) -> Figure:
    """Line chart.

    series: {name: [y, ...]} with a shared x=[...]; or {name: [(x, y), ...]}; or {name: {x: y}}.
    bands: {name: ([lo...], [hi...])} shaded intervals. highlight: name(s) keep their color, others go gray.
    xtick_labels: {x: "label"} (e.g. {0: "0", 1e6: "1M"}) or a list matching xticks.
    xscale: "linear", "category" (x values evenly spaced in order, e.g. doses 0, 1M, 3M, 10M) or "log".
    """
    data = _series(series, x)
    names = list(data)
    unit, _ = resolve_unit(unit)
    hl = as_set(highlight)
    cols = series_colors(len(names), colors, names, highlight=highlight)
    yvals = [v for pts in data.values() for _, v in pts if v is not None]
    if bands:
        for lo_, hi_ in bands.values():
            yvals += [v for v in list(lo_) + list(hi_) if v is not None]
    xs_all = sorted({p[0] for pts in data.values() for p in pts})

    def render(W: float) -> Body:
        H = height or plot_height()
        fmtv = SC.formatter(fmt, decimals, unit, False, yvals)
        if ticks is not None:
            lo, hi, tk = min(ticks), max(ticks), list(ticks)
        elif domain is not None:
            lo, hi, tk = SC.domain(yvals + ([ref] if ref is not None else []), domain[0], domain[1], unit == "%", step=step)
        else:
            lo, hi, tk = SC.domain(yvals + ([ref] if ref is not None else []), percent=unit == "%", zero=zero, step=step)
        tfmt = SC.tick_formatter(tk, unit)
        xt = list(xticks) if xticks is not None else xs_all
        if isinstance(xtick_labels, Mapping):
            xlab = lambda v: xtick_labels.get(v, SC.fmt_num(v, 0, xunit))
        elif xtick_labels is not None:
            m = dict(zip(xt, xtick_labels))
            xlab = lambda v: m.get(v, "")
        else:
            xf = SC.tick_formatter(xt, xunit)
            xlab = xf
        PL = max(T.width(tfmt(t), th.TICK_SIZE) for t in tk) + 14 + (18 if ylabel else 0)
        end_w = 0.0
        if end_labels:
            for nm, pts in data.items():
                last = [p for p in pts if p[1] is not None][-1]
                s = nm + (f"  {fmtv(last[1])}" if end_values else "")
                end_w = max(end_w, T.width(s, 12.5, "sans", 600))
        PR = (end_w + 16) if end_labels else 12
        PT, PB = 12, 30 + (22 if xlabel else 0)
        PW, PH = W - PL - PR, H - PT - PB
        x0, x1 = min(xt + xs_all), max(xt + xs_all)
        if xscale == "category":
            xorder = sorted(set(xt) | set(xs_all))
            X = lambda v: PL + PW * (xorder.index(v) / (len(xorder) - 1) if len(xorder) > 1 else 0.5)
        elif xscale == "log":
            if x0 <= 0:
                raise ValueError("xscale='log' needs x values above 0")
            X = lambda v: PL + PW * (math.log(v / x0) / math.log(x1 / x0) if x1 > x0 else 0.5)
        else:
            X = lambda v: PL + PW * ((v - x0) / (x1 - x0) if x1 > x0 else 0.5)
        Y = lambda v: PT + PH * (1 - (min(max(v, lo), hi) - lo) / (hi - lo))
        out = []
        for t in tk:
            out.append(S.line(PL, Y(t), PL + PW, Y(t), th.AXIS if t == lo else th.GRID))
            out.append(S.text(PL - 10, Y(t) + 4, tfmt(t), th.TICK_SIZE, th.MUTED, "end"))
        for t in xt:
            out.append(S.text(X(t), PT + PH + 20, xlab(t), th.TICK_SIZE, th.MUTED, "middle"))
        if xlabel:
            out.append(S.text(PL + PW / 2, PT + PH + 44, xlabel, 12.5, th.INK2, "middle"))
        if ylabel:
            out.append(S.rotated(13, PT + PH / 2, ylabel, size=12))
        if ref is not None:
            out.append(S.line(PL, Y(ref), PL + PW, Y(ref), th.MUTED, 1, "4 4"))
            if ref_label:
                out.append(S.text(PL + 6, Y(ref) - 6, ref_label, th.MIN_TEXT, th.MUTED))
        order = [i for i, nm in enumerate(names) if hl and nm not in hl] + [i for i, nm in enumerate(names) if not hl or nm in hl]
        for i in order:
            nm, c = names[i], cols[i]
            if bands and nm in bands:
                blo, bhi = bands[nm]
                xs_ = [p[0] for p in data[nm]]
                top = " ".join(f"{S.n(X(a))},{S.n(Y(b))}" for a, b in zip(xs_, bhi) if b is not None)
                bot = " ".join(f"{S.n(X(a))},{S.n(Y(b))}" for a, b in reversed(list(zip(xs_, blo))) if b is not None)
                out.append(f'<polygon points="{top} {bot}" fill="{c}" fill-opacity="0.16"/>')
        ends = []
        for i in order:
            nm, c = names[i], cols[i]
            pts = [(a, b) for a, b in data[nm] if b is not None]
            if not pts:
                continue
            d = "M" + " L".join(f"{S.n(X(a))},{S.n(Y(b))}" for a, b in pts)
            sw = 2.25 if (not hl or nm in hl) else 1.6
            out.append(f'<path d="{d}" fill="none" stroke="{c}" stroke-width="{sw}" stroke-linejoin="round" stroke-linecap="round"/>')
            if markers:
                for a, b in pts:
                    out.append(S.circle(X(a), Y(b), 3.6, c, th.BG, 1.5))
            ends.append([Y(pts[-1][1]), nm, c, pts[-1][1]])
        if end_labels and ends:
            ends.sort(key=lambda e: e[0])
            for k in range(1, len(ends)):  # push overlapping labels apart, then back inside the plot
                ends[k][0] = max(ends[k][0], ends[k - 1][0] + 15)
            over = ends[-1][0] - (PT + PH)
            if over > 0:
                for e in ends:
                    e[0] -= over
            for yy, nm, c, v in ends:
                ink = th.readable(c)  # the series color, darkened only as far as 4.5:1 needs
                parts = [(nm, {"size": 12.5, "weight": 600, "fill": ink})]
                if end_values:
                    parts.append((fmtv(v), {"size": 12.5, "fill": th.INK2, "dx": 6}))
                out.append(S.spans(PL + PW + 10, yy + 4.5, parts))
        return Body("".join(out), H, list(zip(names, cols)), "line")

    return Figure(render, title=title, subtitle=subtitle, legend=legend,
                  legend_position=legend_position, frame=frame, width=width, kind="line")
