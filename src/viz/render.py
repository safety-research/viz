"""Rasterize and print figures with headless Chromium (Playwright), using the vendored fonts.

One browser is started lazily on a dedicated worker thread and reused for every save in the process, so batches
are fast (about 0.1 s a figure after a 1 s start) and it works the same inside Jupyter's event loop.
"""
from __future__ import annotations

import atexit
import base64
import hashlib
import io
import math
import re
import subprocess
import sys
import tempfile
import threading
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
from pathlib import Path

from .text import FONT_DIR
from . import theme as _th

FACES = [  # family, file, style, weight range
    ("DM Sans", "DMSans.ttf", "normal", "100 1000"),
    ("DM Sans", "DMSans-Italic.ttf", "italic", "100 1000"),
    ("Newsreader", "Newsreader.ttf", "normal", "200 800"),
    ("Newsreader", "Newsreader-Italic.ttf", "italic", "200 800"),
    ("JetBrains Mono", "JetBrainsMono.ttf", "normal", "100 800"),
]


def _file_faces() -> str:
    return "".join(f'@font-face{{font-family:"{fam}";src:url("{(FONT_DIR / f).as_uri()}") format("truetype");'
                   f"font-style:{st};font-weight:{wt};font-display:block}}" for fam, f, st, wt in FACES)


def _page(svg: str, w: float, h: float) -> str:
    return (f'<!doctype html><html><head><meta charset="utf-8"><style>{_file_faces()}'
            f"html,body{{margin:0;padding:0;background:{_th.BG}}}svg{{display:block}}</style>"
            f'<style id="viz-page">@page{{size:{w}px {h}px;margin:0}}</style></head><body>{svg}</body></html>')


_SIZE = re.compile(r'<svg[^>]*?width="([\d.]+)"[^>]*?height="([\d.]+)"')
_FONT_PROBES = ["400 13px 'DM Sans'", "600 13px 'DM Sans'", "italic 400 13px 'DM Sans'", "400 16px Newsreader",
                "600 22px Newsreader", "italic 400 16px Newsreader", "400 13px 'JetBrains Mono'",
                "600 13px 'JetBrains Mono'"]


class Renderer:
    """Holds one Chromium page. Use viz.Renderer() as a context manager to control its lifetime yourself."""

    def __init__(self):
        from playwright.sync_api import sync_playwright
        self._pw = sync_playwright().start()
        try:
            self._browser = self._pw.chromium.launch(args=["--no-sandbox"])
        except Exception as e:  # first use in this environment: its Playwright has not downloaded a browser yet
            if "Executable doesn't exist" not in str(e):
                self._pw.stop()
                raise
            print("viz: installing headless Chromium for this Python environment (one time)", file=sys.stderr)
            install_browser()
            self._browser = self._pw.chromium.launch(args=["--no-sandbox"])
        self._pages: dict[float, object] = {}
        self._dir = tempfile.TemporaryDirectory(prefix="viz-")

    def _load(self, svg: str, scale: float):
        m = _SIZE.search(svg)
        w, h = (float(m.group(1)), float(m.group(2))) if m else (1008.0, 800.0)
        pg = self._pages.get(scale)
        if pg is None:  # one page per scale; fonts load once, later figures swap the body in place
            pg = self._browser.new_page(device_scale_factor=scale)
            f = Path(self._dir.name) / f"page{len(self._pages)}.html"
            f.write_text(_page("", w, h))
            pg.goto(f.as_uri(), wait_until="load")
            pg.evaluate("ps => Promise.all(ps.map(p => document.fonts.load(p)))", _FONT_PROBES)
            self._pages[scale] = pg
        pg.set_viewport_size({"width": int(w) + 2, "height": int(h) + 2})
        pg.evaluate("""([svg, w, h]) => {
            document.body.innerHTML = svg;
            document.getElementById('viz-page').textContent = `@page{size:${w}px ${h}px;margin:0}`;
            return document.fonts.ready;
        }""", [svg, w, h])
        return pg, w, h

    def png(self, svg: str, path: Path | None = None, scale: float = 2) -> bytes:
        pg, w, h = self._load(svg, scale)
        data = pg.screenshot(type="png", clip={"x": 0, "y": 0, "width": w, "height": h})
        if path:
            Path(path).write_bytes(data)
        return data

    def html(self, html: str, path: Path | None, width: float, scale: float = 2, fit: bool = False,
             transparent: bool = False) -> bytes:
        """A whole HTML page (with the vendored fonts available) as a PNG of its full height; fit=True crops to the
        page's first element instead (a button, a badge)."""
        pg = self._browser.new_page(device_scale_factor=scale, viewport={"width": int(width), "height": 100})
        try:
            f = Path(self._dir.name) / "page-html.html"
            f.write_text(f'<!doctype html><html><head><meta charset="utf-8"><style>{_file_faces()}'
                         f"html,body{{margin:0;padding:0;background:{'transparent' if transparent else '#FFFFFF'}}}"
                         f"</style></head><body>{html}</body></html>")
            pg.goto(f.as_uri(), wait_until="load")
            pg.evaluate("ps => Promise.all(ps.map(p => document.fonts.load(p)))", _FONT_PROBES)
            pg.evaluate("() => document.fonts.ready")
            if fit:
                box = pg.locator("body > *").first.bounding_box()
                pg.set_viewport_size({"width": int(width), "height": int(box["y"] + box["height"]) + 1})  # a clip
                data = pg.screenshot(type="png", clip=box, omit_background=transparent)  # stops at the viewport
            else:
                h = pg.evaluate("() => Math.ceil(document.body.getBoundingClientRect().height)")
                pg.set_viewport_size({"width": int(width), "height": max(int(h), 1)})
                data = pg.screenshot(type="png", clip={"x": 0, "y": 0, "width": width, "height": h},
                                     omit_background=transparent)
        finally:
            pg.close()
        if path:
            Path(path).write_bytes(data)
        return data

    def pdf(self, svg: str, path: Path) -> bytes:
        pg, w, h = self._load(svg, 1)
        styles = pg.evaluate(_STYLES_JS)  # static fonts and traced halos keep Type 3 fonts out of the PDF (see below)
        faces, families, fonts = static_faces(styles)
        pg.evaluate(_USE_FACES_JS, [faces, families])
        pg.evaluate(_OUTLINE_JS, outline_paths(pg.evaluate(_STROKED_JS), styles, fonts))
        data = pg.pdf(width=f"{w}px", height=f"{h}px", print_background=True,
                      margin={"top": "0", "right": "0", "bottom": "0", "left": "0"}, page_ranges="1")
        Path(path).write_bytes(data)
        return data

    def close(self):
        try:
            self._browser.close()
            self._pw.stop()
        finally:
            self._dir.cleanup()


def install_browser() -> None:
    """Download the headless Chromium that this environment's Playwright drives (once per Playwright version)."""
    subprocess.run([sys.executable, "-m", "playwright", "install", "chromium-headless-shell"], check=True)


# Playwright's sync API owns an event loop on the thread that starts it and refuses to start inside a running
# loop (Jupyter). One dedicated worker thread holds the browser, so scripts and notebooks behave the same.
_executor: ThreadPoolExecutor | None = None
_worker: Renderer | None = None
_lock = threading.Lock()


def _call(method: str, args: tuple):
    global _worker
    if _worker is None:
        _worker = Renderer()
        # atexit runs last in, first out: registered after Renderer() made its temporary directory, close() runs
        # before the weakref exit hook that would otherwise remove the directory, with a ResourceWarning.
        atexit.register(close)
    return getattr(_worker, method)(*args)


def _submit(method: str, *args):
    global _executor
    with _lock:
        if _executor is None:
            _executor = ThreadPoolExecutor(1, thread_name_prefix="viz-render")
    return _executor.submit(_call, method, args).result()


def close() -> None:
    """Shut the shared browser down (also runs at exit)."""
    global _executor
    with _lock:
        ex, _executor = _executor, None
    if ex is None:
        return
    def stop():
        global _worker
        if _worker is not None:
            try:
                _worker.close()
            finally:
                _worker = None
    try:
        ex.submit(stop).result(timeout=20)
    except RuntimeError:  # at exit concurrent.futures has already joined the worker thread, before any atexit hook,
        if _worker is not None:  # so remove the temporary directory from here; Playwright belongs to the dead thread
            _worker._dir.cleanup()
    except Exception:  # best effort at interpreter exit; the browser dies with the process anyway
        pass
    ex.shutdown(wait=False)


def render_png(svg: str, path: Path | None, scale: float = 2) -> bytes:
    return _submit("png", svg, path, scale)


def render_pdf(svg: str, path: Path) -> bytes:
    return _submit("pdf", svg, path)


def render_html(html: str, path: Path | None, width: float, scale: float = 2, fit: bool = False,
                transparent: bool = False) -> bytes:
    """Render an HTML page (figures' SVGs and any layout around them) to a PNG at the given CSS width; fit=True crops
    to the first element, transparent=True keeps the page see-through (for images that sit on any background)."""
    return _submit("html", html, path, width, scale, fit, transparent)


# ---------------------------------------------------------------------- embedded fonts for portable SVG

_TEXT = re.compile(r">([^<>]+)<")


def _chars(svg: str) -> str:
    import html
    return "".join(sorted(set(html.unescape("".join(_TEXT.findall(svg)))))) + " 0123456789%.,+-−"


def font_face_css(svg: str) -> str:
    """@font-face rules with the used glyphs subset and inlined, so the SVG renders the same anywhere."""
    text = _chars(svg)
    used = []
    if "DM Sans" in svg:
        used.append(FACES[0])
        if 'font-style="italic"' in svg:
            used.append(FACES[1])
    if "Newsreader" in svg:
        used.append(FACES[2])
        if 'font-style="italic"' in svg:
            used.append(FACES[3])
    if "JetBrains Mono" in svg:
        used.append(FACES[4])
    out = []
    for fam, f, st, wt in used:
        b64 = base64.b64encode(_cut(f, text)).decode()
        out.append(f'@font-face{{font-family:"{fam}";src:url(data:font/ttf;base64,{b64}) format("truetype");'
                   f"font-style:{st};font-weight:{wt}}}")
    return "".join(out)


@lru_cache(maxsize=32)
def _cut(file: str, chars: str) -> bytes:
    """A vendored font cut down to these characters, with every glyph its layout features reach from them."""
    from fontTools import subset
    from fontTools.ttLib import TTFont
    opts = subset.Options()
    opts.layout_features = ["*"]
    opts.name_IDs = ["*"]
    opts.notdef_outline = True
    sub = subset.Subsetter(opts)
    sub.populate(text=chars)
    buf = io.BytesIO()
    with TTFont(str(FONT_DIR / file), lazy=True) as font:  # lazy=True holds the file open to read tables on demand
        sub.subset(font)
        font.save(buf)
    return buf.getvalue()


# ---------------------------------------------------------------------- PDF without Type 3 fonts
# Chromium writes a variable font into a PDF as Type 3 fonts, which many venues' checks reject. So each text style a
# PDF draws (family, weight, italic, size) gets a static TrueType instance of the vendored font at that weight and
# optical size (Chromium sets the optical size to the font size), which Chromium embeds as TrueType. Stroked text,
# the halo behind a label, comes out as Type 3 whatever the font, so its stroke is traced as a path instead.

_FILES = {(fam, st == "italic"): f for fam, f, st, _ in FACES} | {("JetBrains Mono", True): "JetBrainsMono.ttf"}

# Marks every element that holds text with the index of its style, and returns the styles with their characters.
_STYLES_JS = """() => {
    const styles = [], index = new Map(), skip = new Set(['title', 'desc', 'style', 'script']);
    const walk = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    for (let n = walk.nextNode(); n; n = walk.nextNode()) {
        const el = n.parentElement;
        if (!n.data.length || !el || skip.has(el.localName)) continue;
        const cs = getComputedStyle(el);
        const key = [cs.fontFamily, cs.fontWeight, cs.fontStyle, cs.fontSize].join('|');
        if (!index.has(key)) {
            index.set(key, styles.length);
            styles.push({family: cs.fontFamily, weight: cs.fontWeight, style: cs.fontStyle, size: cs.fontSize, text: ''});
        }
        styles[index.get(key)].text += n.data;
        el.setAttribute('data-viz-style', index.get(key));
    }
    return styles;
}"""

# Swaps the previous figure's static fonts for this one's and points each marked element at its own.
_USE_FACES_JS = """async ([faces, families]) => {
    for (const f of window.vizFaces || []) document.fonts.delete(f);
    window.vizFaces = [];
    for (const {family, data, weight, style} of faces) {
        const face = new FontFace(family, Uint8Array.from(atob(data), c => c.charCodeAt(0)), {weight, style});
        document.fonts.add(await face.load());
        window.vizFaces.push(face);
    }
    for (const el of document.querySelectorAll('[data-viz-style]')) {
        const family = families[el.getAttribute('data-viz-style')];
        if (family) el.style.fontFamily = `"${family}"`;
    }
    await document.fonts.ready;
}"""

# Each stroked <text>: its characters as [style index, character, x, y, rotation]. A text whose characters can't be
# matched to positions (text mixed with tspans, unusual white space) keeps its stroke.
_STROKED_JS = r"""() => {
    const out = [];
    for (const t of document.querySelectorAll('text')) {
        const cs = getComputedStyle(t);
        if (cs.stroke === 'none' || !(parseFloat(cs.strokeWidth) > 0)) continue;
        const kids = [...t.children];
        const parts = kids.length ? kids : [t];
        const own = [...t.childNodes].some(n => n.nodeType === Node.TEXT_NODE && n.data.trim());
        if (kids.length && (own || kids.some(k => k.localName !== 'tspan' || k.children.length))) continue;
        const chars = [];
        let ok = true;
        for (const el of parts) {
            const raw = [...el.childNodes].map(n => n.nodeType === Node.TEXT_NODE ? n.data : '').join('');
            let s = getComputedStyle(el).whiteSpace.startsWith('pre') ? raw.replace(/[\t\n\r]/g, ' ') : raw.replace(/\s+/g, ' ');
            const n = el.getNumberOfChars();
            if (s.length !== n) s = s.trim();
            if (s.length !== n) { ok = false; break; }
            for (let i = 0; i < n; i++) {
                if (s[i] === ' ') continue;
                const p = el.getStartPositionOfChar(i);
                chars.push([+el.getAttribute('data-viz-style'), s[i], p.x, p.y, el.getRotationOfChar(i)]);
            }
        }
        if (!ok) continue;
        t.setAttribute('data-viz-stroke', out.length);
        out.push(chars);
    }
    return out;
}"""

# Draws each marked text's stroke as a path (under the text for paint-order: stroke) and takes the stroke off the text.
_OUTLINE_JS = """(paths) => {
    for (const t of document.querySelectorAll('[data-viz-stroke]')) {
        const cs = getComputedStyle(t);
        const p = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        const attrs = {d: paths[+t.getAttribute('data-viz-stroke')], transform: t.getAttribute('transform'),
                       fill: 'none', stroke: cs.stroke, 'stroke-width': cs.strokeWidth, 'stroke-opacity': cs.strokeOpacity,
                       'stroke-linejoin': cs.strokeLinejoin, 'stroke-miterlimit': cs.strokeMiterlimit};
        for (const [k, v] of Object.entries(attrs)) if (v) p.setAttribute(k, v);
        if (cs.paintOrder.startsWith('stroke')) t.before(p); else t.after(p);
        t.style.stroke = 'none';
    }
}"""


@lru_cache(maxsize=256)
def _static(file: str, chars: str, wght: float, opsz: float) -> bytes:
    """A static instance of the cut font at this weight and optical size, each clamped to the font's range."""
    from fontTools.ttLib import TTFont
    from fontTools.varLib import instancer
    font = TTFont(io.BytesIO(_cut(file, chars)))
    want = {"wght": wght, "opsz": opsz}
    loc = {a.axisTag: min(max(want.get(a.axisTag, a.defaultValue), a.minValue), a.maxValue) for a in font["fvar"].axes}
    instancer.instantiateVariableFont(font, loc, inplace=True)
    buf = io.BytesIO()
    font.save(buf)
    return buf.getvalue()


def static_faces(styles: list[dict]) -> tuple[list[dict], dict[str, str], dict[int, bytes]]:
    """For the text styles _STYLES_JS found: FontFace sources of their static fonts, the family each style index
    takes, and each style's font file. A style in a font viz doesn't bundle keeps its own font."""
    picked, chars = {}, {}
    for i, s in enumerate(styles):
        fam = s["family"].split(",")[0].strip().strip("'\"")
        f = _FILES.get((fam, s["style"] != "normal"))
        if f:
            picked[i] = f
            chars[f] = chars.get(f, " ") + s["text"]
    chars = {f: "".join(sorted(set(t))) for f, t in chars.items()}  # one cut per font file, shared by its styles
    faces: dict[str, dict] = {}
    families, fonts = {}, {}
    for i, f in picked.items():
        s = styles[i]
        data = _static(f, chars[f], float(s["weight"]), float(s["size"].removesuffix("px")))
        style = "italic" if "Italic" in f else "normal"  # JetBrains Mono has no italic: Chromium slants it, as on screen
        family = f"viz-{hashlib.sha1(data).hexdigest()[:12]}-{s['weight']}-{style}"
        faces.setdefault(family, {"family": family, "data": base64.b64encode(data).decode(), "weight": s["weight"],
                                  "style": style})
        families[str(i)] = family
        fonts[i] = data
    return list(faces.values()), families, fonts


def outline_paths(stroked: list[list], styles: list[dict], fonts: dict[int, bytes]) -> list[str]:
    """SVG path data that traces each stroked text's glyphs where Chromium placed them, from the same fonts."""
    from fontTools.pens.recordingPen import DecomposingRecordingPen
    from fontTools.pens.svgPathPen import SVGPathPen
    from fontTools.pens.transformPen import TransformPen
    from fontTools.ttLib import TTFont
    loaded: dict[int, tuple] = {}
    out = []
    for chars in stroked:
        pen = SVGPathPen(None, ntos=lambda v: f"{v:.2f}".rstrip("0").rstrip("."))
        for i, ch, x, y, rot in chars:
            if i not in fonts:
                continue
            if i not in loaded:
                font = TTFont(io.BytesIO(fonts[i]))
                loaded[i] = (font.getGlyphSet(), font.getBestCmap(), font["head"].unitsPerEm)
            glyphs, cmap, upm = loaded[i]
            name = cmap.get(ord(ch))
            if name is None:
                continue
            k = float(styles[i]["size"].removesuffix("px")) / upm
            c, s = math.cos(math.radians(rot)), math.sin(math.radians(rot))
            rec = DecomposingRecordingPen(glyphs)
            glyphs[name].draw(rec)
            rec.replay(TransformPen(pen, (k * c, k * s, k * s, -k * c, x, y)))  # font units, y up -> SVG px, y down
        out.append(pen.getCommands())
    return out
