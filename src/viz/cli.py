"""viz command line.

    viz render spec.json -o fig.png     one spec or a list of specs (JSON); '-' reads stdin
    viz gallery -o out/                 render the gallery of templates (--examples, --readme: their pages)
    viz colors                          print the palette
    viz check spec.json                 list the house rules each spec breaks (exit 1 if any), without rendering
    viz roles                           print the color roles in effect here and the file they came from
    viz path                            print viz's folder, with the templates in examples/ and the docs in docs/
    viz run make_figs.py                run a Python script with the Python that has viz installed
    viz setup                           install the headless Chromium that renders PNG and PDF
    viz --theme dark gallery -o out/    any command in the dark theme (light text on #0D1117)
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def checkout() -> Path | None:
    """The clone this package runs from (an editable install), or None for an installed wheel."""
    root = Path(__file__).resolve().parents[2]
    return root if (root / "pyproject.toml").is_file() and (root / "src" / "viz").is_dir() else None


def home() -> Path:
    """viz's folder, which holds examples/ (the templates) and docs/: the clone for an editable install,
    otherwise the installed package, which ships copies of both."""
    return checkout() or Path(__file__).resolve().parent


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="viz", description="House-style figures: SVG, PNG (2x), PDF.")
    ap.add_argument("--theme", choices=["light", "dark"], help="draw in the light (default) or dark theme")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("render", help="render a JSON spec (or a list of specs)")
    r.add_argument("spec", help="path to a .json spec, or - for stdin")
    r.add_argument("-o", "--out", help="output path (.png .pdf .svg .html); default: next to the spec")
    r.add_argument("--scale", type=float, default=None, help="PNG pixel ratio (default 2)")
    r.add_argument("--alt", action="store_true", help="print each figure's alt text after its path, tab-separated")
    g = sub.add_parser("gallery", help="render every chart type with example data")
    g.add_argument("-o", "--out", default="viz-gallery", help="output folder")
    g.add_argument("--examples", help="also write the examples page (markdown) to this path")
    g.add_argument("--readme", help="also rewrite the gallery block of this README")
    co = sub.add_parser("colors", help="print the color roles and palettes; -o renders the palette card")
    co.add_argument("-o", "--out", help="save the palette card (.png .pdf .svg .html)")
    c = sub.add_parser("check", help="list the house rules a JSON spec (or list of specs) breaks")
    c.add_argument("spec", help="path to a .json spec, or - for stdin")
    sub.add_parser("roles", help="print the color roles in effect here (viz-roles.json) and where they came from")
    sub.add_parser("path", help="print viz's folder: the templates are in examples/, the docs in docs/")
    ru = sub.add_parser("run", help="run a Python script with the Python that has viz installed")
    ru.add_argument("script", help="the script to run")
    ru.add_argument("args", nargs=argparse.REMAINDER, help="arguments for the script")
    sub.add_parser("setup", help="install the headless Chromium that renders PNG and PDF")
    a = ap.parse_args(argv)
    if a.theme:
        from .figure import set_defaults
        set_defaults(theme=a.theme)
    if a.cmd == "render":
        from .spec import render_file
        for p, fig in render_file(a.spec, a.out, a.scale, figures=True):
            print(f"{p}\t{fig.alt_text()}" if a.alt else p)
    elif a.cmd == "gallery":
        from .gallery import build, examples, update_readme
        for p in build(Path(a.out)):
            print(p)
        if a.examples:
            Path(a.examples).write_text(examples())
            print(a.examples)
        if a.readme:
            update_readme(Path(a.readme))
            print(a.readme)
    elif a.cmd == "colors":
        from .colors import ROLES, card
        from .theme import MUTED_SHADES, OUTCOMES, PALETTE, RAMP, SCALES, SERIES
        if a.out:
            print(card().save(a.out))
            return 0
        print("Roles (viz.set_roles or viz-roles.json):")
        for role, name in ROLES.items():
            print(f"  {role:16} {name:6} {PALETTE[name]}")
        print(f"  {'ordered':16} {' to '.join(RAMP)}, light to dark")
        print(f"  {'everything else':16} {', '.join(MUTED_SHADES)} (muted series in turn)")
        print("Outcomes: " + ", ".join(f"{k} {v}" for k, v in OUTCOMES.items()) + "; coral is never a condition")
        print("Series order without roles: " + ", ".join(SERIES) + "; any further series are muted")
        print("Heatmap scales: " + ", ".join(SCALES) + ", diverging (coral below the center, blue above)")
        print("Named colors:")
        for k, v in PALETTE.items():
            print(f"  {k:12} {v}")
    elif a.cmd == "check":
        import json
        from .checks import check
        from .spec import from_spec
        raw = json.loads(sys.stdin.read() if a.spec == "-" else Path(a.spec).read_text())
        bad = 0
        for i, s in enumerate(raw if isinstance(raw, list) else [raw]):
            where = s.get("out") or f"figure {i + 1}"
            for issue in check(from_spec(s), name=where, record=True):
                print(f"{where}: {issue}")
                bad += 1
        if bad:
            return 1
        print("No problems found.")
    elif a.cmd == "roles":
        from .colors import roles, source
        found = source()
        current = roles()
        print(f"From {found}" if found else "No viz-roles.json here or above; set roles in code with viz.set_roles.")
        for label, role in current.items():
            print(f"  {role.split(':')[0]:13} {label}")
    elif a.cmd == "path":
        print(home())
    elif a.cmd == "run":
        return subprocess.run([sys.executable, a.script, *a.args]).returncode
    elif a.cmd == "setup":
        from .render import install_browser
        install_browser()
    return 0


if __name__ == "__main__":
    sys.exit(main())
