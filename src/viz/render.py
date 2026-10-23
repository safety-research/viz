"""Rasterize and print figures with headless Chromium (Playwright), using the vendored fonts.

One browser is started lazily on a dedicated worker thread and reused for every save in the process, so batches
are fast (about 0.1 s a figure after a 1 s start) and it works the same inside Jupyter's event loop.
"""
from __future__ import annotations

import atexit
import base64
import io
import re
import subprocess
import sys
import tempfile
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from .text import FONT_DIR
from .theme import BG

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
            f"html,body{{margin:0;padding:0;background:{BG}}}svg{{display:block}}</style>"
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

    def html(self, html: str, path: Path | None, width: float, scale: float = 2, fit: bool = False) -> bytes:
        """A whole HTML page (with the vendored fonts available) as a PNG of its full height; fit=True crops to the
        page's first element instead (a button, a badge)."""
        pg = self._browser.new_page(device_scale_factor=scale, viewport={"width": int(width), "height": 100})
        try:
            f = Path(self._dir.name) / "page-html.html"
            f.write_text(f'<!doctype html><html><head><meta charset="utf-8"><style>{_file_faces()}'
                         f"html,body{{margin:0;padding:0}}</style></head><body>{html}</body></html>")
            pg.goto(f.as_uri(), wait_until="load")
            pg.evaluate("ps => Promise.all(ps.map(p => document.fonts.load(p)))", _FONT_PROBES)
            pg.evaluate("() => document.fonts.ready")
            if fit:
                data = pg.screenshot(type="png", clip=pg.locator("body > *").first.bounding_box())
            else:
                h = pg.evaluate("() => Math.ceil(document.body.getBoundingClientRect().height)")
                pg.set_viewport_size({"width": int(width), "height": max(int(h), 1)})
                data = pg.screenshot(type="png", clip={"x": 0, "y": 0, "width": width, "height": h})
        finally:
            pg.close()
        if path:
            Path(path).write_bytes(data)
        return data

    def pdf(self, svg: str, path: Path) -> bytes:
        pg, w, h = self._load(svg, 1)
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
    return getattr(_worker, method)(*args)


def _submit(method: str, *args):
    global _executor
    with _lock:
        if _executor is None:
            _executor = ThreadPoolExecutor(1, thread_name_prefix="viz-render")
            atexit.register(close)
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
    except Exception:  # best effort at interpreter exit; the browser dies with the process anyway
        pass
    ex.shutdown(wait=False)


def render_png(svg: str, path: Path | None, scale: float = 2) -> bytes:
    return _submit("png", svg, path, scale)


def render_pdf(svg: str, path: Path) -> bytes:
    return _submit("pdf", svg, path)


def render_html(html: str, path: Path | None, width: float, scale: float = 2, fit: bool = False) -> bytes:
    """Render an HTML page (figures' SVGs and any layout around them) to a PNG at the given CSS width; fit=True crops
    to the first element."""
    return _submit("html", html, path, width, scale, fit)


# ---------------------------------------------------------------------- embedded fonts for portable SVG

_TEXT = re.compile(r">([^<>]+)<")


def _chars(svg: str) -> str:
    import html
    return "".join(sorted(set(html.unescape("".join(_TEXT.findall(svg)))))) + " 0123456789%.,+-−"


def font_face_css(svg: str) -> str:
    """@font-face rules with the used glyphs subset and inlined, so the SVG renders the same anywhere."""
    from fontTools import subset
    from fontTools.ttLib import TTFont
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
        font = TTFont(str(FONT_DIR / f))
        opts = subset.Options()
        opts.layout_features = ["*"]
        opts.name_IDs = ["*"]
        opts.notdef_outline = True
        sub = subset.Subsetter(opts)
        sub.populate(text=text)
        sub.subset(font)
        buf = io.BytesIO()
        font.save(buf)
        b64 = base64.b64encode(buf.getvalue()).decode()
        out.append(f'@font-face{{font-family:"{fam}";src:url(data:font/ttf;base64,{b64}) format("truetype");'
                   f"font-style:{st};font-weight:{wt}}}")
    return "".join(out)
