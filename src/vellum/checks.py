"""Built-in checks: the house rules as feedback. Saving a figure runs them and warns about each problem.

    fig.check()              -> list of problems, [] when the figure follows the rules
    vellum check spec.json   the same for JSON specs, without rendering
    vl.set_defaults(checks="error")   raise instead of warning; "off" skips them

The checks cover what a program can see: the title's shape (one plain sentence, about 10 words, no semicolon,
colon setup, question, dash or intensifier), subtitles (none by default), value labels with more digits than they
need, too many accent colors, colors color-blind readers can't tell apart, and a condition whose color changed
between figures. They can't judge whether the title is true or the chart is the right one.
"""
from __future__ import annotations

import re
import warnings

from . import access
from . import theme as th

TITLE_WORDS = 12          # "about 10 words"
MAX_ACCENTS = 4           # distinct non-neutral colors in one figure
MIN_DELTA_E = 10          # CIEDE2000 distance color-blind readers need to tell two marks apart
INTENSIFIERS = ("dramatically", "drastically", "sharply", "significantly", "substantially", "hugely", "massively",
                "vastly", "greatly", "barely", "strikingly", "surprisingly", "remarkably", "notably", "considerably",
                "far more", "far less", "far fewer", "much more", "much less", "way more", "way less", "skyrocketed",
                "plummeted", "soared", "collapsed", "tanked")
_SUBTITLE_OK = re.compile(r"^(example data|(the )?(error bars|bars|whiskers|bands?|shaded (area|band))\s+"
                          r"(are|is|show|shows)\s+.*interval.*)$", re.I)
_NUMBER = re.compile(r"(?<![\w.])[−+-]?\d[\d,]*\.\d+")
_TEXT = re.compile(r"<text[^>]*>(.*?)</text>", re.S)
_TAG = re.compile(r"<[^>]+>")
_TEXT_KINDS = {"quotes", "episodes", "code_card"}  # their numbers are quoted text, not value labels

_history: dict[str, tuple[str, str]] = {}  # label -> (color, figure it was first seen in)


class VellumCheck(UserWarning):
    """A figure breaks one of the house rules."""


class VellumCheckError(ValueError):
    """Raised on save when vl.set_defaults(checks="error") and a figure breaks a house rule."""


def reset() -> None:
    """Forget the colors earlier figures gave each condition (a new write-up)."""
    _history.clear()


# ---------------------------------------------------------------------------------------------------- the checks

def _title(title: str | None, kind: str, panel: bool = False) -> list[str]:
    if not title:
        return [] if panel or kind in ("code_card",) else ["No title: state the finding in one plain sentence."]
    out = []
    t = title.strip()
    words = len(t.split())
    if not panel and words > TITLE_WORDS:
        out.append(f"Title is {words} words; keep it to about 10.")
    if ";" in t:
        out.append("Title has a semicolon, which means two findings; make two figures.")
    if re.search(r"[A-Za-z)”\"’']: ", t):
        out.append("Title has a colon setup (\"X: Y\"); state the finding as one plain sentence.")
    if "?" in t:
        out.append("Title is a question; state the finding.")
    if re.search(r"\s[—–-]\s|—", t):
        out.append("Title has a dash aside; use one plain sentence.")
    if t.endswith(".") or t.endswith("!"):
        out.append("Drop the punctuation at the end of the title.")
    low = t.lower()
    for w in INTENSIFIERS:
        if re.search(rf"\b{re.escape(w)}\b", low):
            out.append(f"\"{w}\" tells the reader how big without showing it; give the numbers.")
    return out


def _title_fits(fig) -> list[str]:
    """A title should fit on one line at the figure's size: a narrow column takes about half the words of a screen."""
    if not fig.title:
        return []
    from . import text as T
    frame = fig._frame()
    size = fig._size().title if frame == "claim" else th.BLOG_TITLE_SIZE
    n = len(T.wrap(fig.title, fig._width(), size, "serif", 600))
    if n > 1:
        name = fig.size if isinstance(fig.size, str) else "this"
        return [f"Title takes {n} lines at the {name or 'default'} size; shorten it to one line."]
    return []


def _subtitle(subtitle: str | None) -> list[str]:
    if not subtitle:
        return []
    parts = [p.strip() for p in re.split(r"[;.]", subtitle) if p.strip()]
    if all(_SUBTITLE_OK.match(p) for p in parts):
        return []
    return [f"No subtitle by default (\"{subtitle}\"). Put the measure in the axis label or the title and the rest in "
            "the text; keep a subtitle only for \"Example data\" or what the error bars are."]


def _sig_digits(token: str) -> int:
    digits = token.replace(",", "").lstrip("−+-").replace(".", "").lstrip("0")
    return len(digits)


def _round2(token: str) -> str:
    v = float(token.replace(",", "").replace("−", "-"))
    return f"{v:.2g}"


def _decimals(svg: str, skip: set[str]) -> list[str]:
    texts = [" ".join(_TAG.sub(" ", m).split()) for m in _TEXT.findall(svg)]
    tokens = [n for t in texts if t and t not in skip for n in _NUMBER.findall(t)]
    long = [n for n in tokens if _sig_digits(n) > 2]
    if not long:
        return []
    # decimals are fine when rounding to two significant digits would merge values that differ
    rounded: dict[str, set[str]] = {}
    for n in tokens:
        rounded.setdefault(_round2(n), set()).add(n.replace(",", ""))
    needless = [n for n in long if len(rounded[_round2(n)]) == 1]
    if not needless:
        return []
    return [f"Values like {needless[0]} carry more digits than the comparison needs; round to two significant "
            "digits (decimals=0 for percents above 10)."]


def _neutral(hex_: str) -> bool:
    L, a, b = access._lab(hex_)
    return (a * a + b * b) ** 0.5 < 8 or L > 85  # grays, beiges and pale tints are context, not accents


def _colors(assigned: list[tuple[str, str]], name: str, record: bool) -> list[str]:
    out = []
    accents: dict[str, str] = {}  # color -> a label that has it
    for label, c in assigned:
        c = c.upper()
        if c.startswith("#") and len(c) == 7 and not _neutral(c):
            accents.setdefault(c, label)
    if len(accents) > MAX_ACCENTS:
        out.append(f"{len(accents)} accent colors; keep color for what the figure is about and mute the rest "
                   "(vl.set_roles).")
    cols = list(accents)
    for i in range(len(cols)):
        for j in range(i + 1, len(cols)):
            d, kind = access.worst_delta_e(cols[i], cols[j])
            if d < MIN_DELTA_E:
                out.append(f"\"{accents[cols[i]]}\" and \"{accents[cols[j]]}\" look alike with {kind} "
                           f"(distance {d:.0f}); use colors from different palette roles.")
    seen_here: dict[str, str] = {}
    for label, c in assigned:
        c = c.upper()
        if _neutral(c) or label in seen_here:
            continue
        seen_here[label] = c
        before = _history.get(label)
        if before and before[0] != c:
            out.append(f"\"{label}\" is {_name(c)} here but {_name(before[0])} in {before[1]}; give each condition "
                       "one color across a write-up (vl.set_roles).")
    if record:
        for label, c in seen_here.items():
            _history.setdefault(label, (c, name))
    return out


def _name(hex_: str) -> str:
    for k, v in th.PALETTE.items():
        if v.upper() == hex_.upper():
            return k
    return hex_


# ---------------------------------------------------------------------------------------------------- entry points

def check(fig, name: str = "an earlier figure", record: bool = False) -> list[str]:
    """Every rule the figure breaks, as plain sentences. record=True remembers its colors for later figures."""
    issues = _title(fig.title, fig.kind) + _subtitle(fig.subtitle) + _title_fits(fig)
    for child in fig.meta.get("children", []):
        issues += [f"Panel \"{child.title or '?'}\": {p}" for p in _title(child.title, child.kind, panel=True)
                   + _subtitle(child.subtitle)]
    svg = fig.svg()  # composes the figure, which also logs the colors it draws
    if fig.kind not in _TEXT_KINDS:
        skip = {fig.title or "", fig.subtitle or ""}
        issues += _decimals(svg, skip)
    assigned = list(fig.meta.get("colors_made", [])) + list(fig.meta.get("colors_drawn", []))
    for child in fig.meta.get("children", []):
        assigned += list(child.meta.get("colors_made", []))
    issues += _colors(assigned, name, record)
    seen, out = set(), []
    for i in issues:
        if i not in seen:
            seen.add(i)
            out.append(i)
    return out


def on_save(fig, path) -> None:
    """Run by Figure.save: warn (default), raise, or do nothing, per vl.set_defaults(checks=...)."""
    from .figure import defaults
    mode = getattr(defaults, "checks", "warn")
    if mode == "off":
        return
    issues = check(fig, name=getattr(path, "name", str(path)), record=True)
    if not issues:
        return
    if mode == "error":
        raise VellumCheckError(f"{path}: " + " ".join(issues))
    for i in issues:
        warnings.warn(f"vellum check ({getattr(path, 'name', path)}): {i}", VellumCheck, stacklevel=3)
