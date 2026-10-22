"""Number tiles (a 2x2 confusion matrix, or any grid of big numbers) and a 100-square waffle."""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

from .. import svg as S
from .. import text as T
from .. import theme as th
from ..data import pairs
from ..figure import Body, Figure


@dataclass
class Tile:
    """One tile: a big number and a few lines under it. strong=True fills it with the full color (white text);
    otherwise it gets the pale tint of the color."""
    value: str | float
    lines: Sequence[str] = field(default_factory=list)
    color: str = "gray"
    strong: bool = False


def _tile(t) -> Tile:
    if isinstance(t, Tile):
        return t
    if isinstance(t, Mapping):
        return Tile(**t)
    if isinstance(t, (list, tuple)):
        return Tile(*t)
    return Tile(t)


def _fmt(v) -> str:
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        return f"{v:,.0f}" if float(v).is_integer() else f"{v:,}"
    return str(v)


def tiles(grid, *, col_headers=None, row_headers=None, tile_width=None, tile_height=None,
          title=None, subtitle=None, frame=None, width=None) -> Figure:
    """Grid of big-number tiles.

    grid: rows of Tile (or dicts / (value, lines, color, strong) tuples).
    col_headers / row_headers: list of "label" or ("label", "count line").
    """
    rows = [[_tile(t) for t in row] for row in grid]
    ncols = max(len(r) for r in rows)
    norm = lambda hs: [((h, None) if isinstance(h, str) else (h[0], h[1] if len(h) > 1 else None)) for h in hs]
    ch = norm(col_headers) if col_headers else None
    rh = norm(row_headers) if row_headers else None

    def render(W: float) -> Body:
        G = 12
        X0 = (max(max(T.width(a, 15.5, "sans", 600), T.width(b or "", 13)) for a, b in rh) + 18) if rh else 0
        X0 = max(X0, 0.2 * W) if rh else 0
        CW = tile_width or min(330, (W - X0 - G * (ncols - 1)) / ncols)
        max_lines = max((len(t.lines) for r in rows for t in r), default=0)
        CH = tile_height or max(158, 84 + 19 * max_lines + 18)
        Y0 = 64 if ch else 0
        out = []
        cell = lambda c, r: (X0 + c * (CW + G), Y0 + r * (CH + G))
        if ch:
            for c, (lab, cnt) in enumerate(ch):
                x0 = cell(c, 0)[0] + CW / 2
                out.append(S.text(x0, 24, lab, 15.5, th.INK, "middle", 600))
                if cnt:
                    out.append(S.text(x0, 44, cnt, 13, th.MUTED, "middle"))
        if rh:
            for r, (lab, cnt) in enumerate(rh):
                y0 = cell(0, r)[1] + CH / 2
                out.append(S.text(X0 - 18, y0 - 2 if cnt else y0 + 5, lab, 15.5, th.INK, "end", 600))
                if cnt:
                    out.append(S.text(X0 - 18, y0 + 18, cnt, 13, th.MUTED, "end"))
        for r, row in enumerate(rows):
            for c, t in enumerate(row):
                x0, y0 = cell(c, r)
                if t.strong:
                    fill = th.color(t.color)
                    ink, sub = th.text_on(fill), ("#EAF1F8" if th.text_on(fill) == "#FFFFFF" else th.INK2)
                else:
                    fill = th.tint(t.color)
                    ink, sub = th.INK, th.INK2
                out.append(S.rect(x0, y0, CW, CH, fill, 10))
                out.append(S.text(x0 + 22, y0 + 52, _fmt(t.value), 38, ink, weight=600))
                for j, ln in enumerate(t.lines):
                    out.append(S.text(x0 + 22, y0 + 84 + j * 19, ln, 13.5, sub))
        H = Y0 + len(rows) * (CH + G) - G + 4
        return Body("".join(out), H)

    return Figure(render, title=title, subtitle=subtitle, legend=False, frame=frame, width=width,
                  kind="tiles")


def waffle(parts, *, colors=None, total=100, cols=10, count_label=None, notes=None, cell=30,
           title=None, subtitle=None, frame=None, width=None) -> Figure:
    """100 squares split by share, with a big "52 in 100" legend beside them.

    parts: {label: count}. count_label: "reports" adds "(320 reports)" after each label; notes: {label: text}.
    """
    items = pairs(parts)
    n = sum(v for _, v in items)
    raw = [total * v / n for _, v in items]
    sq = [int(x) for x in raw]
    for i in sorted(range(len(raw)), key=lambda i: -(raw[i] - sq[i]))[: total - sum(sq)]:
        sq[i] += 1
    default = ["blue", "light-blue", "beige", "coral", "sage", "gray"]
    cs = [th.color((colors or {}).get(lab) if isinstance(colors, Mapping) else
                   (colors[i] if colors else default[i % len(default)])) for i, (lab, _) in enumerate(items)]

    def render(W: float) -> Body:
        gap = 4
        rows_n = -(-total // cols)
        out = []
        order = [c for c, m in zip(cs, sq) for _ in range(m)]
        for idx, col in enumerate(order):
            r, c = divmod(idx, cols)
            out.append(S.rect(c * (cell + gap), 8 + r * (cell + gap), cell, cell, col, 4))
        LX = cols * (cell + gap) + 44
        for j, ((lab, v), m, col) in enumerate(zip(items, sq, cs)):
            y = 8 + 34 + j * 72
            out.append(S.rect(LX, y - 22, 16, 16, col, 3))
            out.append(S.text(LX + 28, y - 8, f"{m} in {total}", 20, th.INK, weight=600))
            desc = lab
            if notes and lab in notes:
                desc += f" ({notes[lab]})"
            elif count_label:
                desc += f" ({_fmt(v)} {count_label})"
            out.append(S.text(LX + 28, y + 16, desc, 13.5, th.INK2))
        H = max(8 + rows_n * (cell + gap) + 10, 8 + 34 + len(items) * 72 - 30)
        return Body("".join(out), H)

    return Figure(render, title=title, subtitle=subtitle, legend=False, frame=frame, width=width,
                  kind="waffle")
