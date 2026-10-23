"""Figure: a chart body under its title, plus export.

A left-aligned serif claim title, a muted sans subtitle, the legend on top (or below, legend_position="bottom"),
then the chart. No caption under the chart: the house style puts everything in the title and subtitle.
"""
from __future__ import annotations

import hashlib
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path

from . import colors as roles_
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
    size: str | th.Size = "screen"  # screen, slide, paper, column (theme.SIZES), or a viz.Size
    width: float | None = None      # content width in px; None takes it from the size
    scale: float | None = None      # PNG pixel ratio; None takes it from the size (300 dpi for print sizes)
    checks: str = "warn"  # what saving does with a figure that breaks a house rule: warn, error or off
    font: str = "serif"   # chart labels, ticks and legends: "serif" (Newsreader) or "sans" (DM Sans)
    theme: str = "light"  # "dark" draws for a dark page


defaults = Defaults()


def set_defaults(**kw) -> None:
    """viz.set_defaults(size="paper", checks="error")"""
    for k, v in kw.items():
        if k == "frame":  # there is one frame now; older scripts may still set one
            continue
        if not hasattr(defaults, k):
            raise TypeError(f"unknown default {k!r}")
        if k == "theme":
            th.use_theme(v)
        if k == "font":
            if v not in ("serif", "sans"):
                raise ValueError(f"font={v!r}: use 'serif' or 'sans'")
            th.LABEL_FONT = v
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
    legend_position: str | None = None  # top (default) | bottom
    frame: str | None = None  # ignored: there is one frame now, and older scripts may still pass one
    width: float | None = None
    kind: str = "chart"
    meta: dict = field(default_factory=dict)
    roles: dict | None = None  # {label: role} taken when the figure was made (see viz.colors)
    size: str | th.Size | None = None  # screen, slide, paper, column; None follows viz.set_defaults(size=...)

    # ------------------------------------------------------------------ composition
    def _size(self) -> th.Size:
        return th.size_of(self.size or defaults.size)

    def _width(self) -> float:
        return float(self.width or defaults.width or self._size().width - 2 * th.PAD_X)

    def body(self, width: float, inherit: bool = False) -> Body:
        """The chart drawn at this width, with the figure's color roles in effect. inherit=True (a panel inside
        another figure) adds them to the roles already in effect, so the container's roles reach its panels."""
        own = self.roles
        if inherit:
            own = {**roles_.roles(), **(own or {})}
        size = th.current_size() if inherit and self.size is None else self._size()  # panels share their figure's
        token = th._size.set(size)
        try:
            with roles_.using(own), roles_.recording() as log:
                out = self.render(width)
        finally:
            th._size.reset(token)
        self.meta["colors_drawn"] = log
        return out

    def compose(self) -> tuple[str, float, float]:
        """Returns (inner svg, total width, total height)."""
        W = self._width()
        body = self.body(W)
        legend = _legend_items(self.legend, body)
        shape = body.legend_shape
        pos = self.legend_position or "top"
        x0 = th.PAD_X
        y = th.PAD_TOP
        parts: list[str] = []
        if self.title:
            ts = self._size().title
            lines = T.wrap(self.title, W, ts, "serif", 600)
            lh = ts * 1.18
            for i, ln in enumerate(lines):
                parts.append(S.text(x0, y + T.baseline(ts, "serif") + i * lh, ln, ts,
                                    th.INK, family="serif", weight=600))
            y += ts + (len(lines) - 1) * lh + 4
        if self.subtitle:
            lines = T.wrap(self.subtitle, W, th.SUBTITLE_SIZE, "sans")
            lh = T.line_height(th.SUBTITLE_SIZE)
            for i, ln in enumerate(lines):
                parts.append(S.text(x0, y + T.baseline(th.SUBTITLE_SIZE) + i * lh, ln, th.SUBTITLE_SIZE, th.MUTED))
            y += lh * len(lines)
        if self.title or self.subtitle:
            y += th.HEADER_GAP
        if legend and pos == "top":
            svg_, h = legend_block(legend, W, shape=shape)
            parts.append(S.group(svg_, x0, y))
            y += h + th.LEGEND_GAP
        parts.append(S.group(body.svg, x0, y))
        y += body.height
        if legend and pos == "bottom":
            svg_, h = legend_block(legend, W, shape=shape, center=False)
            y += 10
            parts.append(S.group(svg_, x0, y))
            y += h
        y += th.PAD_BOTTOM
        total_w = W + 2 * th.PAD_X
        fixed = self._size().height
        if fixed and y < fixed and self.width is None:  # slides fill the 16:9 frame
            y = fixed
        return "".join(parts), total_w, y

    # ------------------------------------------------------------------ outputs
    def check(self) -> list[str]:
        """The house rules this figure breaks, as plain sentences ([] when it follows them)."""
        from .checks import check
        return check(self)

    def alt_text(self) -> str:
        """The figure in words, for screen readers and for an image's alt attribute: the title, then the data."""
        title = (self.title or "").strip()
        parts = [title if title.endswith((".", "?", "!")) or not title else title + ".", self.meta.get("alt") or ""]
        return " ".join(p for p in parts if p)

    def svg(self, embed_fonts: bool = False, background: bool = True) -> str:
        """The whole figure as one SVG document, with its title and alt text for screen readers."""
        inner, w, h = self.compose()
        label = S.esc(self.title or self.kind)
        style = ""
        if embed_fonts:
            from .render import font_face_css
            style = f"<defs><style>{font_face_css(inner)}</style></defs>"
        bg = S.rect(0, 0, w, h, th.BG) if background else ""
        alt = self.meta.get("alt")
        key = hashlib.sha1(f"{self.title}|{alt}|{inner}".encode()).hexdigest()[:10]  # same figure, same ids
        tid, did = f"viz-title-{key}", f"viz-desc-{key}"
        title = f'<title id="{tid}">{label}</title>'
        desc = f'<desc id="{did}">{S.esc(alt)}</desc>' if alt else ""
        names = f"{tid} {did}" if alt else tid
        sz = self._size()
        pw, ph = (sz.inches * 96, h * sz.inches * 96 / w) if sz.inches else (w, h)  # print sizes: true inches (96 px/in)
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{S.n(pw)}" height="{S.n(ph)}" '
                f'viewBox="0 0 {S.n(w)} {S.n(h)}" role="img" aria-labelledby="{names}">{title}{desc}{style}{bg}{inner}'
                f"</svg>")

    def html(self, standalone: bool = True) -> str:
        """Inline-SVG HTML. standalone=False gives a <figure> fragment to paste into an artifact page."""
        svg_ = self.svg()
        _, w, _ = self.compose()
        fig = (f'<figure class="viz" style="margin:0;overflow-x:auto;-webkit-overflow-scrolling:touch">'
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
        from .checks import on_save
        on_save(self, p)  # the house rules as warnings (viz.set_defaults(checks=...))
        p.parent.mkdir(parents=True, exist_ok=True)
        ext = p.suffix.lower()
        if ext == ".svg":
            p.write_text(self.svg(embed_fonts=True))
        elif ext in (".html", ".htm"):
            p.write_text(self.html())
        elif ext == ".png":
            from .render import render_png
            render_png(self.svg(), p, scale or self._png_scale())
        elif ext == ".pdf":
            from .render import render_pdf
            render_pdf(self.svg(), p)
        else:
            raise ValueError(f"unknown extension {ext!r}: use .png, .pdf, .svg or .html")
        return p

    def png(self, scale: float | None = None) -> bytes:
        from .render import render_png
        return render_png(self.svg(), None, scale or self._png_scale())

    def _png_scale(self) -> float:
        sz = self._size()
        return defaults.scale or (th.DPI / 96 if sz.inches else sz.scale)

    def _repr_svg_(self) -> str:  # Jupyter
        return self.svg(embed_fonts=True)


# ---------------------------------------------------------------------- shared blocks

def legend_block(items: list[tuple[str, str]], width: float, shape: str = "square",
                 center: bool = False) -> tuple[str, float]:
    """Legend rows in the label font, with rounded swatches."""
    fam, size, sw, gap_in, gap_out, rx, row_gap = "sans", th.LEGEND_SIZE, 12, 8, 22, 3, 8
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
