"""Likert chart: diverging stacked bars for answers on an ordered scale, from Strongly disagree to Strongly agree or a
model's -3..+3 self-report.

Each row is shown as percent of its answers. Answers below the neutral point extend left of a center line, the most
extreme farthest out, and answers above it extend right; the neutral answers straddle the line, half on each side.
The colors are the outcome colors: coral shades below the neutral point and blue shades above it, stronger toward
the extremes, and beige for the neutral answers. The scale's labels sit in a legend row above the bars, in scale
order, and each bar carries its low share at its left end and its high share at its right end.
"""
from __future__ import annotations

import bisect
import math
from collections.abc import Mapping

from .. import access
from .. import data as D
from .. import scale as SC
from .. import svg as S
from .. import text as T
from .. import theme as th
from ..figure import Body, Figure

PALE, DEEP = 0.5, 0.4  # how far the weakest shade mixes toward the background, and the strongest toward the ink
STEP = 20.0            # CIEDE2000 between neighbouring shades below which the extreme moves past the palette color


def shades(name: str, k: int) -> list[str]:
    """k shades of a palette color from weak (next to the center line) to strong (the extreme), evenly spaced in
    CIEDE2000: from the color mixed toward the background to the color itself, and on toward the ink when k shades
    need the room to stay apart. Mixed with the theme's tokens, so they follow the theme."""
    c = th.color(name)
    if k <= 1:
        return [c] * k
    n = 48
    us = [-1 + 2 * i / n for i in range(n + 1)]
    at = lambda u: th.mix(c, th.BG, -u * PALE) if u < 0 else th.mix(c, th.INK, u * DEEP)
    pts = [at(u) for u in us]
    arc = [0.0]
    for p, q in zip(pts, pts[1:]):
        arc.append(arc[-1] + access.delta_e(p, q))
    end = min(max(arc[n // 2], STEP * (k - 1)), arc[-1])
    out = []
    for i in range(k):
        target = end * i / (k - 1)
        j = min(max(bisect.bisect_left(arc, target), 1), n)
        t = min(max((target - arc[j - 1]) / ((arc[j] - arc[j - 1]) or 1), 0.0), 1.0)
        out.append(at(us[j - 1] + (us[j] - us[j - 1]) * t))
    return out


def sides(n: int, mid: int | None) -> tuple[list[int], list[int]]:
    """The indices of the scale points below and above the neutral one (an even scale splits in the middle)."""
    if mid is None:
        return list(range(n // 2)), list(range(n // 2, n))
    return list(range(mid)), list(range(mid + 1, n))


def fills(n: int, mid: int | None, low: str | None = None, high: str | None = None) -> list[str]:
    """The fill of each scale point, low to high: shades of `low` below the neutral point (strongest at the low end),
    the neutral outcome color for it, shades of `high` above it. low and high default to the bad and good outcome
    colors (theme.OUTCOMES: coral and blue)."""
    lows, highs = sides(n, mid)
    neutral = [th.color(th.OUTCOMES["neutral"])] if mid is not None else []
    return (shades(low or th.OUTCOMES["bad"], len(lows))[::-1] + neutral
            + shades(high or th.OUTCOMES["good"], len(highs)))


def split(r, n: int, mid: int | None) -> tuple[float, float, float] | None:
    """A row's summed shares below and above the neutral point, and its neutral share; None without answers."""
    if r.values[0] is None:
        return None
    lows, highs = sides(n, mid)
    return (sum(r.values[i] for i in lows), sum(r.values[i] for i in highs),
            r.values[mid] if mid is not None else 0.0)


def net(r, n: int, mid: int | None) -> float | None:
    """High share minus low share, what sort=True ranks rows by (None for a row without answers)."""
    s = split(r, n, mid)
    return None if s is None else s[1] - s[0]


def _label(v, signed: bool) -> str:
    """A scale point as the legend writes it: numbers get a true minus, and a plus when the scale has negatives."""
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        return f"{SC.MINUS if v < 0 else '+' if signed and v > 0 else ''}{abs(v):g}"
    return str(v)


def answers(data, scale, neutral=None, sort=False):
    """(rows, scale labels, neutral index or None): each data row's values as percents of its answers, or None
    throughout when it has none, in the order the chart draws them."""
    if scale is None or isinstance(scale, str):
        raise ValueError("scale: the answer categories from low to high, such as ['Disagree', 'Neutral', 'Agree']")
    points = list(scale)
    signed = any(isinstance(v, (int, float)) and not isinstance(v, bool) and v < 0 for v in points)
    labels = [_label(v, signed) for v in points]
    n = len(labels)
    if n < 2 or len(set(labels)) != n:
        raise ValueError("scale needs at least two different categories, from low to high")
    where = {}  # the forms a scale point may take: as given, as text, as the legend writes it
    for i, v in enumerate(points):
        for key in (v, str(v), labels[i]):
            where.setdefault(key, i)
    if neutral is None:
        mid = n // 2 if n % 2 else None  # an odd scale's middle category is its neutral point
    elif neutral in where or str(neutral) in where:
        mid = where.get(neutral, where.get(str(neutral)))
    else:
        raise ValueError(f"neutral={neutral!r} isn't one of the scale's categories: {', '.join(labels)}")
    items = data
    if not D._is_frame(data):  # {row: {scale point: count}}, such as a Counter of answers, becomes counts in order
        items = []
        for it in (data.items() if hasattr(data, "items") else data):
            if isinstance(it, (tuple, list)) and len(it) == 2 and isinstance(it[1], Mapping):
                counts = [0.0] * n
                for key, v in it[1].items():
                    i = where.get(key, where.get(str(key)))
                    if i is None:
                        raise ValueError(f"row {it[0]!r} has answers {key!r}, which aren't on the scale")
                    counts[i] += float(v)
                it = (it[0], counts)
            items.append(it)
    rows, _ns, _ = D.rows(items)
    for r in rows:
        if r.section:
            continue
        if len(r.values) != n:
            raise ValueError(f"row {r.label!r} has {len(r.values)} values for the {n} points of the scale")
        if any(v is not None and v < 0 for v in r.values):
            raise ValueError(f"row {r.label!r} has a negative count")
        total = sum(v or 0 for v in r.values)
        r.values = [100 * (v or 0) / total for v in r.values] if total > 0 else [None] * n
    if sort:
        if any(r.section for r in rows):
            raise ValueError("sort=True can't be combined with sections")
        sign = -1 if sort != "asc" else 1
        rows.sort(key=lambda r: (net(r, n, mid) is None, sign * (net(r, n, mid) or 0)))
    return rows, labels, mid


def order_facts(data, scale=None, neutral=None, **_) -> dict | None:
    """What the order check reads: the row labels and their net shares (high minus low)."""
    rows, labels, mid = answers(data, scale, neutral)
    if any(r.section for r in rows):
        return None
    return {"labels": [r.label for r in rows], "keys": [net(r, len(labels), mid) for r in rows]}


def describe(data, scale=None, neutral=None, sort=False, decimals=None, fmt=None, **_) -> str:
    """Alt text: every row's shares by scale point, then its low and high totals."""
    rows, labels, mid = answers(data, scale, neutral, sort)
    f = SC.formatter(fmt, 0 if decimals is None else decimals, "%")
    head = f"Diverging stacked bars of answers from {labels[0]} to {labels[-1]}"
    head += f", {labels[mid]} as neutral" if mid is not None else ""
    out, section = [], None
    for r in rows:
        if r.section:
            section = r.label
            continue
        if r.values[0] is None:
            item = f"{r.label}: no answers"
        else:
            lo, hi, _neu = split(r, len(labels), mid)
            item = (f"{r.label}: " + ", ".join(f"{lab} {f(v)}" for lab, v in zip(labels, r.values))
                    + f" ({f(lo)} below the middle, {f(hi)} above it)")
        if section:
            item, section = f"{section}: {item}", None
        out.append(item)
    return f"{head}. {'; '.join(out)}."


def likert(data, *, scale, neutral=None, sort=False, totals=True, low=None, high=None, decimals=None, fmt=None,
           values=True, axis=True, xlabel=None, row_height=40, bar_height=24, label_width=None,
           title=None, subtitle=None, legend=None, legend_position="top", frame=None, width=None) -> Figure:
    """Diverging stacked bars for answers on an ordered scale.

    data: {row: [count per scale point]} in scale order, counts or shares (each row is drawn as percent of its
          total), {row: {scale point: count}} (a Counter of answers works), a list of (row, counts) pairs that may
          include viz.section("heading") rows, or a pandas DataFrame with one column per scale point.
    scale: the category labels from low to high, such as ["Strongly disagree", ..., "Strongly agree"] or
           range(-3, 4) (numbers are written with a true minus, and a plus when the scale has negatives).
    neutral: the middle category, which straddles the center line; None takes an odd scale's middle category and
             splits an even scale in half.
    sort: True orders rows by net share (high minus low), largest first; "asc" smallest first.
    totals: write the summed low share at each bar's left end and the high share at its right end.
    low, high: the colors of the two sides, by default the bad and good outcome colors (coral below, blue above);
               pass low="blue", high="coral" when the high answers are the bad ones.
    decimals/fmt: the percent labels (whole percents by default). values=False drops the labels inside segments.
    axis=False drops the percent axis under the bars (0 at the center line); xlabel names it.
    """
    rows, labels, mid = answers(data, scale, neutral, sort)
    n = len(labels)
    data_rows = [r for r in rows if not r.section]
    if not data_rows:
        raise ValueError("likert needs at least one row of answers")
    fmtv = SC.formatter(fmt, 0 if decimals is None else decimals, "%")
    tot = {id(r): split(r, n, mid) for r in data_rows if r.values[0] is not None}

    def render(W: float) -> Body:
        cols = fills(n, mid, low, high)
        ink_low, ink_high = th.readable(low or th.OUTCOMES["bad"]), th.readable(high or th.OUTCOMES["good"])

        # ---- label column, as in hbar
        ls = 13.5
        max_lab = label_width or 0.42 * W
        lab_lines = {r.label: (T.wrap_balanced(r.label, max_lab, ls) if T.width(r.label, ls) > max_lab else [r.label])
                     for r in data_rows}
        L = max((T.width(ln, ls) for lines in lab_lines.values() for ln in lines), default=40) + 14
        if label_width:
            L = label_width + 14
        L = max(L, 0.24 * W)

        # ---- domain: as far left and right as the bars reach, in quarters (halves when quarters would crowd)
        reach_l = max((lo + neu / 2 for lo, _hi, neu in tot.values()), default=0.0)
        reach_r = max((hi + neu / 2 for _lo, hi, neu in tot.values()), default=0.0)
        steps = lambda st: math.ceil(reach_l / st - 1e-9) + math.ceil(reach_r / st - 1e-9)
        st = 25.0 if steps(25.0) * 64 <= W - L else 50.0
        lo_, hi_ = -st * math.ceil(reach_l / st - 1e-9), st * math.ceil(reach_r / st - 1e-9)
        if lo_ == hi_:
            lo_, hi_ = -st, st
        tk = [lo_ + i * st for i in range(round((hi_ - lo_) / st) + 1)]
        tfmt = SC.tick_formatter([abs(t) for t in tk], "%")

        # ---- center C and scale k (px per percent): the widest k that keeps the axis, and each bar with its
        # totals, between the label column and the right edge. Each bound is linear in k: C >= p + q k, C <= r - s k.
        gap = 8
        tw = lambda v: T.width(fmtv(v), 13, "sans", 600)
        lower = [(L, -lo_)]
        upper = [(W - (T.width(tfmt(hi_), th.TICK_SIZE) / 2 + 2 if axis else 0), hi_)]
        if totals:
            for lo, hi, neu in tot.values():
                lower.append((L + gap + tw(lo), lo + neu / 2))
                upper.append((W - gap - tw(hi), hi + neu / 2))
        k = min(((r - p) / (q + s) for p, q in lower for r, s in upper if q + s > 0), default=1.0)
        k = max(k, 0.5)
        C = max(p + q * k for p, q in lower)
        x = lambda v: C + k * v

        # ---- rows
        top = 4
        y = top
        layout = []
        for r in rows:
            h = 32 if r.section else max(row_height, len(lab_lines[r.label]) * ls * 1.25 + 8)
            layout.append((r, y, h))
            y += h
        bottom = y
        out, labels_svg = [], []
        if axis:
            for t in tk:
                if t != 0:
                    out.append(S.line(x(t), top, x(t), bottom, th.GRID))
                out.append(S.text(x(t), bottom + 20, tfmt(abs(t)), th.TICK_SIZE, th.MUTED, "middle"))
        out.append(S.line(x(0), top, x(0), bottom, th.AXIS, 1.2))  # the center line, behind the bars
        for r, yy, h in layout:
            if r.section:
                out.append(S.text(0, yy + 24, r.label, 13, th.MUTED, weight=600))
                continue
            lines = lab_lines[r.label]
            lh = ls * 1.25
            first = yy + h / 2 - (len(lines) - 1) * lh / 2 + ls * 0.36
            for i, ln in enumerate(lines):
                out.append(S.text(L - 14, first + i * lh, ln, ls, th.INK2, "end"))
            if id(r) not in tot:
                labels_svg.append(S.text(x(0), yy + h / 2 + 4.3, "no answers", 12, th.MUTED, "middle", halo=th.BG))
                continue
            lo, hi, neu = tot[id(r)]
            by = yy + (h - bar_height) / 2
            acc = -(lo + neu / 2)
            segs = [(j, v) for j, v in enumerate(r.values) if v > 0]
            for m, (j, v) in enumerate(segs):
                xa, xb = x(acc), x(acc + v)
                if len(segs) == 1:
                    out.append(S.rect(xa, by, xb - xa, bar_height, cols[j], min(4, (xb - xa) / 2)))
                elif m == 0:  # the outer ends are rounded, as every bar's data end is
                    out.append(S.hbar(xb + 0.4, by, xa, bar_height, cols[j]))
                elif m == len(segs) - 1:
                    out.append(S.hbar(xa, by, xb, bar_height, cols[j]))
                else:
                    out.append(S.rect(xa, by, xb - xa + 0.4, bar_height, cols[j]))
                txt = fmtv(v)
                if values and T.width(txt, 12, "sans", 600) + 8 <= xb - xa:
                    labels_svg.append(S.text((xa + xb) / 2, by + bar_height / 2 + 4.3, txt, 12, th.text_on(cols[j]),
                                             "middle", 600))
                acc += v
            if totals:
                ty = by + bar_height / 2 + 4.8
                labels_svg.append(S.text(x(-(lo + neu / 2)) - gap, ty, fmtv(lo), 13, ink_low, "end", 600))
                labels_svg.append(S.text(x(hi + neu / 2) + gap, ty, fmtv(hi), 13, ink_high, weight=600))
        out += labels_svg
        height = bottom + (30 if axis else 6)
        if xlabel:
            out.append(S.text(x((lo_ + hi_) / 2), bottom + (46 if axis else 22), xlabel, 12.5, th.INK2, "middle"))
            height += 24 if axis else 22
        return Body("".join(out), height, list(zip(labels, cols)), meta={"plot_x": (x(lo_), x(hi_))})

    return Figure(render, title=title, subtitle=subtitle, legend=legend if legend is not None else True,
                  legend_position=legend_position, frame=frame, width=width, kind="likert")
