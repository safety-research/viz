"""vellum command line.

    vellum render spec.json -o fig.png     one spec or a list of specs (JSON); '-' reads stdin
    vellum gallery -o out/                 render the example gallery
    vellum colors                          print the palette
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="vellum", description="House-style figures: SVG, PNG (2x), PDF.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("render", help="render a JSON spec (or a list of specs)")
    r.add_argument("spec", help="path to a .json spec, or - for stdin")
    r.add_argument("-o", "--out", help="output path (.png .pdf .svg .html); default: next to the spec")
    r.add_argument("--scale", type=float, default=None, help="PNG pixel ratio (default 2)")
    g = sub.add_parser("gallery", help="render every chart type with example data")
    g.add_argument("-o", "--out", default="vellum-gallery", help="output folder")
    sub.add_parser("colors", help="print the named colors")
    a = ap.parse_args(argv)
    if a.cmd == "render":
        from .spec import render_file
        for p in render_file(a.spec, a.out, a.scale):
            print(p)
    elif a.cmd == "gallery":
        from .gallery import build
        for p in build(Path(a.out)):
            print(p)
    elif a.cmd == "colors":
        from .theme import PALETTE
        for k, v in PALETTE.items():
            print(f"{k:12} {v}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
