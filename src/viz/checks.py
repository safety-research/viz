"""Built-in checks: the house rules as feedback. Saving a figure runs them and warns about each problem.

    fig.check()              -> list of problems, [] when the figure follows the rules
    viz check spec.json   the same for JSON specs, without rendering
    viz.set_defaults(checks="error")   raise instead of warning; "off" skips them

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
_TEXT_KINDS = {"quotes", "episodes", "code_card", "chat", "tokens"}  # their numbers are quoted text, not value labels

_history: dict[tuple[str, str], tuple[str, str]] = {}  # (theme, label) -> (color, figure it was first seen in)


class VizCheck(UserWarning):
    """A figure breaks one of the house rules."""


class VizCheckError(ValueError):
    """Raised on save when viz.set_defaults(checks="error") and a figure breaks a house rule."""


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


ORDER_KINDS = ("hbar", "bars", "dotplot", "likert")


def order_facts(kind: str, args: tuple, kw: dict) -> dict | None:
    """What the order check needs from a chart call: its category labels and the value each is ranked by. None when
    the chart has no categories to order, or when the call chose the order itself (any sort= at all)."""
    if kind not in ORDER_KINDS or "sort" in kw:
        return None
    from . import data as D
    from .charts.common import sort_key
    try:
        if kind == "likert":  # rows ranked by net share, high minus low
            from .charts.likert import order_facts as likert_facts
            return likert_facts(*args, **kw)
        rows, _ns, names = D.rows(args[0] if args else kw.get("data"), kw.get("series"))
    except Exception:
        return None
    if any(r.section for r in rows):
        return None
    names = list(kw["series"]) if kw.get("series") is not None else names
    return {"labels": [r.label for r in rows], "keys": [sort_key(r.values, names) for r in rows]}


def _order(fig) -> list[str]:
    """Categories read best in order of their values; models, sizes and steps have an order of their own."""
    from .charts.common import looks_like_models
    figs = [fig, *fig.meta.get("children", [])]
    named = _named(fig)
    out = []
    for f in figs:
        facts = f.meta.get("order")
        if not facts:
            continue
        labels, keys = facts["labels"], [k for k in facts["keys"] if k is not None]
        if len(keys) < 3 or looks_like_models(labels) or any(str(named.get(x, "")).startswith("ordered:") for x in labels):
            continue
        if all(a <= b for a, b in zip(keys, keys[1:])) or all(a >= b for a, b in zip(keys, keys[1:])):
            continue
        where = f"Panel \"{f.title}\": " if f is not fig and f.title else ""
        out.append(f"{where}The categories aren't in order of their values. Sort them (sort=True: largest first; "
                   "\"asc\" for smallest first) unless the order means something, such as model release, size or "
                   "training step; sort=False keeps it without this warning.")
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


def _named(fig) -> dict[str, str]:
    """Every {label: role} the figure and its panels were made with."""
    named = dict(fig.roles or {})
    for child in fig.meta.get("children", []):
        named.update(child.roles or {})
    return named


def _roles(fig, assigned) -> list[str]:
    """Roles are matched by exact label, so flag a figure where none match and labels that look like a role's."""
    named = _named(fig)
    if not named:
        return []
    labels = list(dict.fromkeys(lab for lab, _c, _s in assigned))
    if not labels:
        return []
    if not any(lab in named for lab in labels):
        shown = ", ".join(f'"{lab}"' for lab in labels[:3])
        return [f"Roles are set, but none of this figure's labels has one ({shown}); check that the names match "
                "viz.set_roles exactly."]
    muted = {th.color(m).upper() for m in th.MUTED_SHADES}
    out = []
    def plain(s: str) -> str:  # "With search (n=400)" and "with-search" both read "with search"
        s = re.sub(r"[\(\[].*?[\)\]]", " ", s.lower())
        return " ".join(re.sub(r"[^a-z0-9]+", " ", s).split())
    for lab in dict.fromkeys(lab for lab, c, sp in assigned if not sp and c.upper() in muted and lab not in named):
        near = next((k for k in named if plain(k) == plain(lab)), None)
        if near:
            out.append(f"\"{lab}\" has no role, so it is muted, but it looks like \"{near}\" ({named[near].split(':')[0]}); "
                       "name it in the roles if it should stand out.")
    return out


def _colors(assigned, name: str, record: bool, named: dict[str, str] | None = None) -> list[str]:
    out = []
    accents: dict[str, str] = {}  # color -> a label that has it
    assigned = [(lab, c) for lab, c, specific in assigned if specific]
    ordered = {lab for lab, role in (named or {}).items() if role.startswith("ordered:")}
    if any(lab in ordered for lab, _ in assigned):
        accents["ordered"] = "the ordered conditions"  # one light-to-dark family, built to step evenly in one hue
    for label, c in assigned:
        c = c.upper()
        if label not in ordered and c.startswith("#") and len(c) == 7 and not _neutral(c):
            accents.setdefault(c, label)
    if len(accents) > MAX_ACCENTS:
        out.append(f"{len(accents)} accent colors; keep color for what the figure is about and mute the rest "
                   "(viz.set_roles).")
    # one color must mean one thing: labels that share a color should share a role (several interventions may)
    by_color: dict[str, dict[str, str]] = {}
    for label, c in assigned:
        if not _neutral(c.upper()):
            role = (named or {}).get(label, "its own color").split(":")[0]
            by_color.setdefault(c.upper(), {}).setdefault(role, label)
    for c, kinds in by_color.items():
        if len(kinds) > 1:
            (r1, l1), (r2, l2) = list(kinds.items())[:2]
            out.append(f"\"{l1}\" ({r1}) and \"{l2}\" ({r2}) share one color, so a reader can't tell them apart; "
                       "give them different roles' colors.")
    cols = [c for c in accents if c != "ordered"]
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
        before = _history.get((th.THEME, label))  # the dark theme redraws the grays and the ramp
        if before and before[0] != c:
            out.append(f"\"{label}\" is {_name(c)} here but {_name(before[0])} in {before[1]}; give each condition "
                       "one color across a write-up (viz.set_roles).")
    if record:
        for label, c in seen_here.items():
            _history.setdefault((th.THEME, label), (c, name))
    return out


def _name(hex_: str) -> str:
    for k, v in th.PALETTE.items():
        if v.upper() == hex_.upper():
            return k
    return hex_


# ---------------------------------------------------------------------------------------------------- entry points

def check(fig, name: str = "an earlier figure", record: bool = False) -> list[str]:
    """Every rule the figure breaks, as plain sentences. record=True remembers its colors for later figures."""
    issues = _title(fig.title, fig.kind) + _subtitle(fig.subtitle) + _title_fits(fig) + _order(fig)
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
    issues += _roles(fig, assigned)
    issues += _colors(assigned, name, record, _named(fig))
    seen, out = set(), []
    for i in issues:
        if i not in seen:
            seen.add(i)
            out.append(i)
    return out


def on_save(fig, path) -> None:
    """Run by Figure.save: warn (default), raise, or do nothing, per viz.set_defaults(checks=...)."""
    from .figure import defaults
    mode = getattr(defaults, "checks", "warn")
    if mode == "off":
        return
    issues = check(fig, name=getattr(path, "name", str(path)), record=True)
    if not issues:
        return
    if mode == "error":
        raise VizCheckError(f"{path}: " + " ".join(issues))
    for i in issues:
        warnings.warn(f"viz check ({getattr(path, 'name', path)}): {i}", VizCheck, stacklevel=3)
