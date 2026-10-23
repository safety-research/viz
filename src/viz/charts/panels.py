"""Panels: several charts in a grid under one title, with one shared legend."""
from __future__ import annotations

from .. import svg as S
from .. import text as T
from .. import theme as th
from ..figure import Body, Figure


def panels(figs: list[Figure], *, cols: int = 2, gap: float | None = None, row_gap: float | None = None,
           title=None, subtitle=None, legend=None, legend_position=None, width=None) -> Figure:
    """Lay out charts in a grid. Each chart's own title becomes its panel title, centered over its plot.
    The legend is shared: the union of the panels' legends unless you pass one."""
    figs = list(figs)
    if not figs:
        raise ValueError("panels() needs at least one figure")
    cols = max(1, min(cols, len(figs)))

    def render(W: float) -> Body:
        g = gap if gap is not None else 32
        rg = row_gap if row_gap is not None else 26
        pw = (W - g * (cols - 1)) / cols
        bodies = [f.body(pw, inherit=True) for f in figs]
        for start in range(0, len(figs), cols):  # vertical bars in one row share their category-label depth
            row = list(range(start, min(start + cols, len(figs))))
            depth = max((bodies[i].meta.get("cat_lines", 0) for i in row), default=0)
            for i in row:
                if "cat_lines" in bodies[i].meta and bodies[i].meta["cat_lines"] < depth:
                    figs[i].meta["cat_lines"] = depth
                    try:
                        bodies[i] = figs[i].body(pw, inherit=True)
                    finally:
                        figs[i].meta.pop("cat_lines", None)
        cells = []
        for f, body in zip(figs, bodies):
            parts, h = [], 0.0
            # centered titles sit over the chart's plot area when it reports one (vertical bars do), not over the tick
            # margin: as close to the plot's center as the panel's edges allow, wrapped only when wider than the panel
            px0, px1 = body.meta.get("plot_x", (0.0, pw))
            mid = (px0 + px1) / 2

            def centered(text, size, fam="sans", wt=400):
                lines = T.wrap(text, pw, size, fam, wt)
                if len(lines) > 1:
                    lines = T.wrap_balanced(text, pw, size, fam, wt)
                w = max(T.width(ln, size, fam, wt) for ln in lines)
                return lines, min(max(mid, w / 2), pw - w / 2)
            if f.title:  # centered over the panel's plot
                size, fam, wt = 14, "sans", 600
                lh = T.line_height(size, fam)
                lines, x = centered(f.title, size, fam, wt)
                for i, ln in enumerate(lines):
                    parts.append(S.text(x, h + T.baseline(size, fam) + i * lh, ln, size, th.INK, "middle", wt, fam))
                h += T.line_height(size, fam) + (len(lines) - 1) * lh
                h += 6
            if f.subtitle:
                size = 12.5
                lines, x = centered(f.subtitle, size)
                for i, ln in enumerate(lines):
                    parts.append(S.text(x, h + T.baseline(size) + i * T.line_height(size), ln, size, th.MUTED, "middle"))
                h += len(lines) * T.line_height(size) + 4
            cells.append(("".join(parts), h, body))
        out = []
        y = 0.0
        for start in range(0, len(cells), cols):
            row = cells[start:start + cols]
            th_max = max(c[1] for c in row)
            bh_max = max(c[2].height for c in row)
            for k, (tsvg, th_, body) in enumerate(row):
                x0 = k * (pw + g)
                out.append(S.group(tsvg, x0, y + th_max - th_))
                out.append(S.group(body.svg, x0, y + th_max))
            y += th_max + bh_max + rg
        y -= rg
        merged: list[tuple[str, str]] = []
        seen = set()
        for f, (_, _, body) in zip(figs, cells):
            items = body.legend or []
            if f.legend not in (None, True, False):
                from .figure import _legend_items
                items = _legend_items(f.legend, body)
            for lab, col in items:
                if lab not in seen:
                    seen.add(lab)
                    merged.append((lab, col))
        shape = cells[0][2].legend_shape
        return Body("".join(out), y, merged or None, shape)

    lp = legend_position
    return Figure(render, title=title, subtitle=subtitle, legend=legend if legend is not None else True,
                  legend_position=lp, width=width, kind="panels")
