"""Results table as a figure, in the booktabs look: a rule above the header, one under it and one at the bottom, no
vertical lines, and generous row spacing.

Row labels are left-aligned and numbers right-aligned with tabular figures. The best value in each column is bold,
an interval follows its value in small muted type, and a highlighted row sits on a pale tint of its role color.
viz.section("Open models") rows group the rows under muted headings.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from .. import data as D
from .. import scale as SC
from .. import svg as S
from .. import text as T
from .. import theme as th
from ..figure import Body, Figure
from .common import UNSET, as_set, resolve_unit, row_colors

DASH = "—"                  # a missing value
PAD = 8                     # the rules reach this far past the text on each side
CI_GAP = 5                  # between a value and its interval
MIN_GAP, MAX_GAP = 28, 200  # between columns: the table spreads toward the figure's width, up to MAX_GAP apart
RULES = (1.2, 0.75)         # booktabs: heavy rules at the top and bottom, a light one under the header
TABULAR = 'style="font-variant-numeric:tabular-nums"'
GOALS = ("higher", "lower", None)


@dataclass
class Cells:
    """What the table shows, worked out once for the figure and its alt text."""
    rows: list            # D.Row, sections kept
    cols: list[str]
    corner: str | None    # the label column's header
    text: dict            # id(row) -> [value text per column]
    bold: dict            # id(row) -> [best in its column]
    ci: dict              # id(row) -> [interval text or None per column]
    ci_words: dict        # id(row) -> [(lo, hi) as text with the unit, or None], for the alt text


def _each(opt, cols: list[str], name: str, default=None) -> list:
    """An option for every column, or {column: value} for some of them: one value per column."""
    if isinstance(opt, Mapping):
        opt = {str(k): v for k, v in opt.items()}
        unknown = [k for k in opt if k not in cols]
        if unknown:
            raise ValueError(f"{name} names columns that aren't in the table: {', '.join(unknown)}")
        return [opt.get(c, default) for c in cols]
    return [opt] * len(cols)


def _rows(rows, columns):
    """(rows with sections kept, column labels, the label column's header from a DataFrame's index name)."""
    if D._is_frame(rows):
        out, ns, names = D.rows(rows)
        cols = [str(c) for c in columns] if columns is not None else list(names or [])
        corner = rows.index.name
    else:
        items = list(rows.items()) if hasattr(rows, "items") else list(rows)
        pair = lambda it: isinstance(it, (tuple, list)) and len(it) == 2
        pairs = [it for it in items if pair(it)]
        mapped = bool(pairs) and all(isinstance(v, Mapping) for _, v in pairs)
        if columns is None:
            if not mapped:
                raise ValueError("pass columns=[...]: the header of each value column")
            columns = list(dict.fromkeys(str(c) for _, v in pairs for c in v))
        cols = [str(c) for c in columns]
        if mapped:  # {row: {column: value}}
            items = [(it[0], [{str(k): x for k, x in it[1].items()}.get(c) for c in cols]) if pair(it) else it
                     for it in items]
        out, ns, _ = D.rows(items)
        corner = None
    if all(r.section for r in out):
        raise ValueError("table needs at least one row")
    if ns != len(cols):
        raise ValueError(f"{len(cols)} columns for {ns} values per row")
    return out, cols, corner


def cells(rows, columns=None, better=None, unit=UNSET, decimals=None, fmt=None, signed=False, ci=None,
          label_header=None, **_) -> Cells:
    """Every cell's text, which values are the best in their column, and the intervals' text."""
    rs, cols, corner = _rows(rows, columns)
    nc = len(cols)
    data_rows = [r for r in rs if not r.section]
    goals = ["higher"] * nc if better is None else _each(better, cols, "better", "higher")
    for g in goals:
        if g not in GOALS:
            raise ValueError(f"better={g!r}: use 'higher', 'lower' or None (no best in that column)")
    units = [resolve_unit(u) for u in _each(unit, cols, "unit", UNSET)]
    SC.check_percent([r.values[j] for j, (u, given) in enumerate(units) if u == "%" and not given for r in data_rows],
                     "%", False)
    decs, fmts = _each(decimals, cols, "decimals"), _each(fmt, cols, "fmt")
    if isinstance(ci, Mapping):
        known = {r.label for r in data_rows}
        unknown = [str(k) for k in ci if str(k) not in known]
        if unknown:
            raise ValueError(f"ci names rows that aren't in the table: {', '.join(unknown)}")
    try:
        D.attach_ci(rs, ci, nc)
    except (TypeError, IndexError):
        raise ValueError("ci: {row: [(lo, hi) or None per column]}") from None
    for r in data_rows:
        if r.ci and len(r.ci) != nc:
            raise ValueError(f"ci for {r.label!r} has {len(r.ci)} intervals for {nc} columns")

    text = {id(r): [None] * nc for r in data_rows}
    bold = {id(r): [False] * nc for r in data_rows}
    lohi: dict[int, list] = {id(r): [None] * nc for r in data_rows}
    words: dict[int, list] = {id(r): [None] * nc for r in data_rows}  # the same with the unit, for the alt text
    pm_ok, ci_fmt = True, []
    for j in range(nc):
        vals = [r.values[j] for r in data_rows]
        u = units[j][0]
        d = decs[j]
        if d is None and fmts[j] is None:
            d = 0 if u == "%" else SC.decimals_for(vals, u)  # percents in whole numbers, as the heatmap writes them
        f = SC.formatter(fmts[j], d, u, signed, vals)
        for r in data_rows:
            text[id(r)][j] = DASH if r.values[j] is None else f(r.values[j])
        have = [r for r in data_rows if r.values[j] is not None]
        if goals[j] and len({text[id(r)][j] for r in have}) > 1:  # bold every value that reads as the best one
            pick = max if goals[j] == "higher" else min
            best = f(pick(r.values[j] for r in have))
            for r in have:
                bold[id(r)][j] = text[id(r)][j] == best
        # intervals: written with enough decimals to show their width, without the unit
        ints = [(r.values[j], r.ci[j]) for r in data_rows if r.ci and r.ci[j] is not None]
        dc = d or 0
        while fmts[j] is None and dc < (d or 0) + 2 and any(round((hi - lo) / 2, dc) == 0 for _, (lo, hi) in ints):
            dc += 1
        if fmts[j] is None:
            cf = lambda v, dc_=dc: SC.fmt_num(v, dc_, "", signed)
            half = lambda v, dc_=dc: SC.fmt_num(abs(v), dc_)
            word = lambda v, dc_=dc, u_=u: SC.fmt_num(v, dc_, u_, signed)
        else:
            cf = word = f
            half = lambda v, f_=f: f_(abs(v))
        ci_fmt.append((cf, half))
        for r in data_rows:
            c = r.ci[j] if r.ci else None
            if c is None:
                continue
            lohi[id(r)][j] = (cf(c[0]), cf(c[1]))
            words[id(r)][j] = (word(c[0]), word(c[1]))
            v = r.values[j]
            if v is None or not c[0] <= v <= c[1] or half(c[1] - v) != half(v - c[0]):
                pm_ok = False
    # one form for the whole table: ±x when every interval is symmetric as written, else [lo, hi]
    ci_text = {id(r): [None] * nc for r in data_rows}
    for r in data_rows:
        for j, pair in enumerate(lohi[id(r)]):
            if pair is not None:
                ci_text[id(r)][j] = f"±{ci_fmt[j][1](r.ci[j][1] - r.values[j])}" if pm_ok else f"[{pair[0]}, {pair[1]}]"
    return Cells(rs, cols, label_header if label_header is not None else corner, text, bold, ci_text, words)


def describe(rows, **kw) -> str:
    """Alt text: the columns, then each row's values with their intervals, the best in each column marked."""
    c = cells(rows, **kw)
    marks = "; bold marks the best in each column" if any(any(b) for b in c.bold.values()) else ""
    out, section = [], None
    for r in c.rows:
        if r.section:
            section = r.label
            continue
        parts = []
        for j, col in enumerate(c.cols):
            t = "no value" if r.values[j] is None else c.text[id(r)][j]
            if c.ci_words[id(r)][j]:
                t += f" (interval {c.ci_words[id(r)][j][0]} to {c.ci_words[id(r)][j][1]})"
            if c.bold[id(r)][j]:
                t += " (best)"
            parts.append(f"{col} {t}")
        item = f"{r.label}: " + ", ".join(parts)
        if section:
            item, section = f"{section}: {item}", None
        out.append(item)
    n = sum(not r.section for r in c.rows)
    return f"Table of {n} rows by {len(c.cols)} columns ({', '.join(c.cols)}{marks}). {'; '.join(out)}."


def table(rows, *, columns=None, better=None, unit=UNSET, decimals=None, fmt=None, signed=False, ci=None,
          highlight=None, accent="intervention", label_header=None, title=None, subtitle=None, frame=None,
          width=None) -> Figure:
    """A results table in the booktabs look.

    rows: {row label: [value per column]}, {row label: {column: value}}, a list of (label, values) pairs that may
          include viz.section("Open models") rows, or a pandas DataFrame. None prints an em dash.
    columns: the header of each value column (taken from a DataFrame or from {column: value} rows when left out).
    better: {column: "higher" | "lower" | None}, or one of them for every column; "higher" by default. The best value
            in each column is bold (every value that reads the same as the best, and none when all read the same).
    ci: {row: [(lo, hi) or None per column]}, written small and muted after the value: ±x when every interval is
        symmetric as written, else [lo, hi].
    highlight: row label(s) set on a pale tint of their role color (viz.set_roles), else of the accent, with a bold
               label.
    unit, decimals, fmt: as in the other charts (percent by default, in whole percents), once for every column or as
                         {column: value}; signed=True writes a plus on positive values, for changes.
    label_header: the header over the row labels, such as "Model" (a DataFrame's index name by default).
    """
    c = cells(rows, columns=columns, better=better, unit=unit, decimals=decimals, fmt=fmt, signed=signed, ci=ci,
              label_header=label_header)
    rs, cols, nc = c.rows, c.cols, len(c.cols)
    data_rows = [r for r in rs if not r.section]
    hl = as_set(highlight)
    unknown = sorted(hl - {r.label for r in data_rows})
    if unknown:
        raise ValueError(f"highlight names rows that aren't in the table: {', '.join(unknown)}")

    def render(W: float) -> Body:
        marked = [lab for lab in dict.fromkeys(r.label for r in data_rows) if lab in hl]
        named = lambda col: next((k for k, v in th.PALETTE.items() if v.upper() == col.upper()), col)
        tint = {lab: th.tint(named(col)) for lab, col in  # the theme's own pale fill when the color has one
                zip(marked, row_colors(marked, highlight=marked, accent=accent) if marked else [])}

        # ---- widths: the largest text that fits, headers wrapped only when the columns need the room
        cs = 12.0  # intervals
        lab_wt = lambda r: 600 if r.label in tint else 400
        for vs in (13.5, 12.5, 12.0):
            max_lab = 0.4 * W
            lab_lines = {id(r): (T.wrap_balanced(r.label, max_lab, vs, "sans", lab_wt(r))
                                 if T.width(r.label, vs, "sans", lab_wt(r)) > max_lab else [r.label]) for r in data_rows}
            lab_w = max([T.width(ln, vs, "sans", lab_wt(r)) for r in data_rows for ln in lab_lines[id(r)]]
                        + [T.width(c.corner, vs, "sans", 600) if c.corner else 0])
            val_w = [max(T.width(c.text[id(r)][j], vs, "sans", 600 if c.bold[id(r)][j] else 400) for r in data_rows)
                     for j in range(nc)]
            ci_w = [max((T.width(c.ci[id(r)][j], cs) for r in data_rows if c.ci[id(r)][j]), default=0.0)
                    for j in range(nc)]
            content = [val_w[j] + (CI_GAP + ci_w[j] if ci_w[j] else 0) for j in range(nc)]
            head = [T.width(col, vs, "sans", 600) for col in cols]
            words = [max(T.width(w, vs, "sans", 600) for w in col.split() or [""]) for col in cols]

            def widths(cap: float) -> list[float]:  # each column with its header wrapped at cap, never inside a word
                return [max([content[j]] + [T.width(ln, vs, "sans", 600) for ln in
                                            T.wrap(col, max(cap, words[j]) / T.SAFETY + 0.5, vs, "sans", 600)])
                        for j, col in enumerate(cols)]
            room = lambda cw, g: 2 * PAD + lab_w + sum(cw) + nc * g <= W
            colw = [max(content[j], head[j]) for j in range(nc)]
            if not room(colw, MIN_GAP):  # wrap the headers as little as comfortable gaps allow, else to their words
                colw = widths(0.0)
                for g in (2 * MIN_GAP, MIN_GAP):
                    if room(colw, g):
                        lo, hi = 0.0, max(head)
                        for _ in range(16):
                            m = (lo + hi) / 2
                            lo, hi = (m, hi) if room(widths(m), g) else (lo, m)
                        colw = widths(lo)
                        break
            if room(colw, MIN_GAP):
                break
        head_lines = [T.wrap(col, colw[j] / T.SAFETY + 0.5, vs, "sans", 600) for j, col in enumerate(cols)]
        gap = min(MAX_GAP, max(MIN_GAP, (W - 2 * PAD - lab_w - sum(colw)) / nc))
        TW = 2 * PAD + lab_w + sum(colw) + nc * gap
        X0 = (W - TW) / 2 if TW < W and fig._frame() == "blog" else 0.0  # centered under a centered title
        blocks, xx = [], X0 + PAD + lab_w
        for j in range(nc):
            xx += gap
            blocks.append(xx)
            xx += colw[j]

        # ---- rows of text, top to bottom
        lh = vs * 1.25
        nl = max(len(h) for h in head_lines)
        out, ink = [], []
        y = RULES[0]
        head_top = y + 8
        base = lambda top, size, h: top + T.baseline(size, "sans", h)
        if c.corner:
            ink.append(S.text(X0 + PAD, base(head_top + (nl - 1) * lh, vs, lh), c.corner, vs, th.INK, weight=600))
        for j, lines in enumerate(head_lines):
            cx = blocks[j] + colw[j] / 2
            for i, ln in enumerate(lines):
                ink.append(S.text(cx, base(head_top + (nl - len(lines) + i) * lh, vs, lh), ln, vs, th.INK, "middle",
                                  600))
        mid = head_top + nl * lh + 7
        y = mid + RULES[1] / 2 + 3
        rh = round(vs * 2.4)
        seps = []
        for k, r in enumerate(rs):
            if r.section:
                if k and not rs[k - 1].section:  # a light rule between groups
                    seps.append(y + 4)
                    y += 6
                ink.append(S.text(X0 + PAD, y + 22, r.label, 13, th.MUTED, weight=600))
                y += 30
                continue
            lines = lab_lines[id(r)]
            h = max(rh, len(lines) * vs * 1.25 + 12)
            bg = tint.get(r.label)
            if bg:
                out.append(S.rect(X0, y, TW, h, bg))
            soft = th.readable(th.MUTED, bg) if bg else th.MUTED
            first = y + (h - len(lines) * lh) / 2
            for i, ln in enumerate(lines):
                ink.append(S.text(X0 + PAD, base(first + i * lh, vs, lh), ln, vs, th.INK if bg else th.INK2,
                                  weight=600 if bg else 400))
            ty = base(y, vs, h)
            for j in range(nc):
                right = blocks[j] + (colw[j] + content[j]) / 2  # the content sits centered under its header
                xv = right - (CI_GAP + ci_w[j] if ci_w[j] else 0)
                if r.values[j] is None:
                    ink.append(S.text(xv, ty, DASH, vs, soft, "end"))
                    continue
                b = c.bold[id(r)][j]
                ink.append(S.text(xv, ty, c.text[id(r)][j], vs, th.INK if b else th.INK2, "end", 600 if b else 400))
                if c.ci[id(r)][j]:
                    ink.append(S.text(xv + CI_GAP, ty, c.ci[id(r)][j], cs, soft))
            y += h
        bottom = y + 3 + RULES[0] / 2
        out.append(S.line(X0, RULES[0] / 2, X0 + TW, RULES[0] / 2, th.INK, RULES[0]))
        out.append(S.line(X0, mid, X0 + TW, mid, th.INK, RULES[1]))
        for sy in seps:
            out.append(S.line(X0, sy, X0 + TW, sy, th.AXIS, RULES[1]))
        out.append(S.line(X0, bottom, X0 + TW, bottom, th.INK, RULES[0]))
        body = S.group("".join(out + ink), extra=TABULAR)
        return Body(body, bottom + RULES[0] / 2 + 2, None, meta={"plot_x": (X0, X0 + TW)})

    fig = Figure(render, title=title, subtitle=subtitle, legend=False, frame=frame, width=width, kind="table")
    return fig
