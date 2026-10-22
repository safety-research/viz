"""Figure: a chart body inside one of the two frames, plus export.

claim frame (default): left-aligned serif claim title, muted sans subtitle, legend on top, chart.
blog frame: centered serif title and subtitle, chart, centered legend below.
Neither frame draws a caption under the chart: the house style puts everything in the title and subtitle.
"""
from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path

from . import svg as S
from . import text as T
from . import theme as th


@dataclass
class Body:
    """What a chart draws at a given width: SVG in local coordinates (0..width) and its height."""
    svg: str
    height: float
    legend: list[tuple[str, str]] | None = None
    legend_shape: str = "square"  # square | round | line
    meta: dict = field(default_factory=dict)  # layout facts a container may align across panels


@dataclass
class Defaults:
    frame: str = "claim"
    width: float = th.WIDTH
    scale: float = 2


defaults = Defaults()


def set_defaults(**kw) -> None:
    """vl.set_defaults(frame="blog", width=900, scale=3)"""
    for k, v in kw.items():
        if not hasattr(defaults, k):
            raise TypeError(f"unknown default {k!r}")
        setattr(defaults, k, v)


LegendSpec = Mapping[str, str] | Sequence[tuple[str, str]] | bool | None


def _legend_items(spec: LegendSpec, body: Body | None) -> list[tuple[str, str]]:
    if spec is False:
        return []
    if spec is None or spec is True:
        items = (body.legend if body else None) or []
        return items if (spec is True or len(items) > 1) else []
    if isinstance(spec, Mapping):
        return [(str(k), th.color(v)) for k, v in spec.items()]
    return [(str(k), th.color(v)) for k, v in spec]


@dataclass
class Figure:
    render: Callable[[float], Body]
    title: str | None = None
    subtitle: str | None = None
    legend: LegendSpec = None
    legend_position: str | None = None  # top | bottom (frame default)
    frame: str | None = None
    width: float | None = None
    kind: str = "chart"
    meta: dict = field(default_factory=dict)

    # ------------------------------------------------------------------ composition
    def _frame(self) -> str:
        return self.frame or defaults.frame

    def _width(self) -> float:
        return float(self.width or defaults.width)

    def compose(self) -> tuple[str, float, float]:
        """Returns (inner svg, total width, total height)."""
        W = self._width()
        frame = self._frame()
        body = self.render(W)
        legend = _legend_items(self.legend, body)
        shape = body.legend_shape
        pos = self.legend_position or ("top" if frame == "claim" else "bottom")
        x0 = th.PAD_X
        y = th.PAD_TOP
        parts: list[str] = []
        if frame == "claim":
            if self.title:
                lines = T.wrap(self.title, W, th.TITLE_SIZE, "serif", 600)
                lh = th.TITLE_SIZE * 1.18
                for i, ln in enumerate(lines):
                    parts.append(S.text(x0, y + T.baseline(th.TITLE_SIZE, "serif") + i * lh, ln, th.TITLE_SIZE,
                                        th.INK, family="serif", weight=600))
                y += th.TITLE_SIZE + (len(lines) - 1) * lh + 4
            if self.subtitle:
                lines = T.wrap(self.subtitle, W, th.SUBTITLE_SIZE, "sans")
                lh = T.line_height(th.SUBTITLE_SIZE)
                for i, ln in enumerate(lines):
                    parts.append(S.text(x0, y + T.baseline(th.SUBTITLE_SIZE) + i * lh, ln, th.SUBTITLE_SIZE, th.MUTED))
                y += lh * len(lines)
            if self.title or self.subtitle:
                y += th.HEADER_GAP
            if legend and pos == "top":
                svg_, h = legend_block(legend, W, shape=shape, style="claim")
                parts.append(S.group(svg_, x0, y))
                y += h + th.LEGEND_GAP
            parts.append(S.group(body.svg, x0, y))
            y += body.height
            if legend and pos == "bottom":
                svg_, h = legend_block(legend, W, shape=shape, style="claim", center=False)
                y += 10
                parts.append(S.group(svg_, x0, y))
                y += h
        else:  # blog
            if self.title:
                lines = T.wrap(self.title, W, th.BLOG_TITLE_SIZE, "serif", 600)
                lh = th.BLOG_TITLE_SIZE * 1.2
                for i, ln in enumerate(lines):
                    parts.append(S.text(x0 + W / 2, y + T.baseline(th.BLOG_TITLE_SIZE, "serif") + i * lh, ln,
                                        th.BLOG_TITLE_SIZE, th.INK, "middle", 600, "serif"))
                y += th.BLOG_TITLE_SIZE + (len(lines) - 1) * lh + 6
            if self.subtitle:
                lines = T.wrap(self.subtitle, W, 13, "sans")
                lh = T.line_height(13)
                for i, ln in enumerate(lines):
                    parts.append(S.text(x0 + W / 2, y + T.baseline(13) + i * lh, ln, 13, th.MUTED, "middle"))
                y += lh * len(lines) + 8
            if legend and pos == "top":
                svg_, h = legend_block(legend, W, shape=shape, style="blog", center=True)
                parts.append(S.group(svg_, x0, y))
                y += h + 8
            parts.append(S.group(body.svg, x0, y))
            y += body.height
            if legend and pos == "bottom":
                y += 6
                svg_, h = legend_block(legend, W, shape=shape, style="blog", center=True)
                parts.append(S.group(svg_, x0, y))
                y += h
        y += th.PAD_BOTTOM
        total_w = W + 2 * th.PAD_X
        return "".join(parts), total_w, y

    # ------------------------------------------------------------------ outputs
    def svg(self, embed_fonts: bool = False, background: bool = True) -> str:
        """The whole figure as one SVG document."""
        inner, w, h = self.compose()
        label = S.esc(self.title or self.kind)
        style = ""
        if embed_fonts:
            from .render import font_face_css
            style = f"<defs><style>{font_face_css(inner)}</style></defs>"
        bg = S.rect(0, 0, w, h, th.BG) if background else ""
        title = f"<title>{label}</title>" if self.title else ""
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{S.n(w)}" height="{S.n(h)}" '
                f'viewBox="0 0 {S.n(w)} {S.n(h)}" role="img" aria-label="{label}">{title}{style}{bg}{inner}</svg>')

    def html(self, standalone: bool = True) -> str:
        """Inline-SVG HTML. standalone=False gives a <figure> fragment to paste into an artifact page."""
        svg_ = self.svg()
        _, w, _ = self.compose()
        fig = (f'<figure class="vellum" style="margin:0;overflow-x:auto;-webkit-overflow-scrolling:touch">'
               f'<div style="min-width:{int(min(w, 640))}px">'
               + svg_.replace("<svg ", '<svg style="display:block;width:100%;height:auto" ', 1) + "</div></figure>")
        link = f'<link rel="stylesheet" href="{th.GOOGLE_FONTS}">'
        if not standalone:
            return link + fig
        return (f'<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, '
                f'initial-scale=1"><title>{S.esc(self.title or "figure")}</title>{link}<style>body{{margin:0;'
                f'background:{th.BG}}}main{{max-width:{int(w)}px;margin:0 auto;padding:16px}}</style></head>'
                f"<body><main>{fig}</main></body></html>")

    def save(self, path: str | Path, scale: float | None = None) -> Path:
        """Write .png (2x by default), .pdf (vector), .svg (fonts embedded) or .html, by extension."""
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        ext = p.suffix.lower()
        if ext == ".svg":
            p.write_text(self.svg(embed_fonts=True))
        elif ext in (".html", ".htm"):
            p.write_text(self.html())
        elif ext == ".png":
            from .render import render_png
            render_png(self.svg(), p, scale or defaults.scale)
        elif ext == ".pdf":
            from .render import render_pdf
            render_pdf(self.svg(), p)
        else:
            raise ValueError(f"unknown extension {ext!r}: use .png, .pdf, .svg or .html")
        return p

    def png(self, scale: float | None = None) -> bytes:
        from .render import render_png
        return render_png(self.svg(), None, scale or defaults.scale)

    def _repr_svg_(self) -> str:  # Jupyter
        return self.svg(embed_fonts=True)


# ---------------------------------------------------------------------- shared blocks

def legend_block(items: list[tuple[str, str]], width: float, shape: str = "square", style: str = "claim",
                 center: bool = False) -> tuple[str, float]:
    """Legend rows. claim: sans 13 with rounded swatches; blog: serif 13 with square swatches, centered."""
    if style == "claim":
        fam, size, sw, gap_in, gap_out, rx, row_gap = "sans", th.LEGEND_SIZE, 12, 8, 22, 3, 8
    else:
        fam, size, sw, gap_in, gap_out, rx, row_gap = "serif", 13, 12, 9, 26, 0, 10
    lh = T.line_height(size, fam)
    row_h = max(lh, sw)
    widths = [sw + gap_in + T.width(lab, size, fam) for lab, _ in items]
    rows: list[list[int]] = [[]]
    cur = 0.0
    for i, w in enumerate(widths):
        add = w if not rows[-1] else gap_out + w
        if rows[-1] and cur + add > width:
            rows.append([i])
            cur = w
        else:
            rows[-1].append(i)
            cur += add
    out = []
    for r, idxs in enumerate(rows):
        total = sum(widths[i] for i in idxs) + gap_out * (len(idxs) - 1)
        x = (width - total) / 2 if center else 0.0
        top = r * (row_h + row_gap)
        for i in idxs:
            lab, col = items[i]
            sy = top + (row_h - sw) / 2
            if shape == "round":
                out.append(S.circle(x + sw / 2, sy + sw / 2, sw / 2 - 0.5, col))
            elif shape == "line":
                out.append(S.line(x, sy + sw / 2, x + sw + 4, sy + sw / 2, col, 2.5, cap="round"))
            else:
                out.append(S.rect(x, sy, sw, sw, col, rx))
            out.append(S.text(x + sw + gap_in, top + T.baseline(size, fam, row_h), lab, size, th.INK2, family=fam))
            x += widths[i] + gap_out
    return "".join(out), len(rows) * row_h + (len(rows) - 1) * row_gap
