"""Axis domains, ticks and number formatting."""
from __future__ import annotations

import math
import warnings
from collections.abc import Callable, Iterable

MINUS = "−"


def nice_step(span: float, target: int = 5) -> float:
    if span <= 0:
        return 1.0
    raw = span / target
    mag = 10 ** math.floor(math.log10(raw))
    for m in (1, 2, 2.5, 5, 10):
        if m * mag >= raw * 0.999:
            return m * mag
    return 10 * mag


def _round(v: float, step: float) -> float:
    d = max(0, -math.floor(math.log10(step)) + 2) if step < 1 else 0
    return round(v, d + 2)


def domain(values: Iterable[float | None], lo: float | None = None, hi: float | None = None, percent: bool = False,
           target: int = 5, zero: bool = True, step: float | None = None, full_percent_step: float = 25,
           ) -> tuple[float, float, list[float]]:
    """Nice (lo, hi, ticks) covering the values. Percent data above 75 gets the full 0-100 scale."""
    vals = [float(v) for v in values if v is not None and not (isinstance(v, float) and math.isnan(v))]
    if not vals:
        vals = [0.0, 1.0]
    vmin, vmax = min(vals), max(vals)
    if zero:
        vmin, vmax = min(vmin, 0.0), max(vmax, 0.0)
    if lo is not None and hi is not None:
        st = step or nice_step(hi - lo, target)
        return lo, hi, ticks(lo, hi, st)
    if percent and vmin >= 0 and vmax > 75 and vmax <= 100 and hi is None:
        st = step or full_percent_step
        lo_ = 0.0 if lo is None else lo
        return lo_, 100.0, ticks(lo_, 100.0, st)
    a = vmin if lo is None else lo
    b = vmax if hi is None else hi
    if a == b:
        b = a + 1
    st = step or nice_step(b - a, target)
    lo_ = lo if lo is not None else math.floor(a / st + 1e-9) * st
    hi_ = hi if hi is not None else math.ceil(b / st - 1e-9) * st
    if percent and hi is None and hi_ > 100 and vmax <= 100:
        hi_ = 100.0
    if hi_ == lo_:
        hi_ = lo_ + st
    return _round(lo_, st), _round(hi_, st), ticks(lo_, hi_, st)


def ticks(lo: float, hi: float, step: float) -> list[float]:
    out, k = [], 0
    while True:
        v = lo + k * step
        if v > hi + step * 1e-6:
            break
        out.append(_round(v, step))
        k += 1
    return out


def decimals_for(values: Iterable[float | None], unit: str = "") -> int:
    vals = [v for v in values if v is not None]
    if all(float(v).is_integer() for v in vals):
        return 0
    return 1 if unit == "%" else 2


def fmt_num(v: float, decimals: int = 0, unit: str = "", signed: bool = False, thousands: bool = True) -> str:
    body = f"{abs(v):,.{decimals}f}" if thousands else f"{abs(v):.{decimals}f}"
    if v < 0 and float(body.replace(",", "")) != 0:
        sign = MINUS
    elif signed and v > 0 and float(body.replace(",", "")) != 0:
        sign = "+"
    else:
        sign = ""
    return f"{sign}{body}{unit}"


def formatter(fmt: str | Callable[[float], str] | None = None, decimals: int | None = None, unit: str = "",
              signed: bool = False, values: Iterable[float | None] = ()) -> Callable[[float], str]:
    """Value-label formatter: a format string ('{:.1f}%'), a callable, or automatic decimals + unit."""
    if callable(fmt):
        return fmt
    if isinstance(fmt, str):
        return lambda v: fmt.format(v)
    d = decimals_for(values, unit) if decimals is None else decimals
    return lambda v: f"0{unit}" if v == 0 else fmt_num(v, d, unit, signed)


def tick_formatter(tick_values: list[float], unit: str = "", signed: bool = False,
                   fmt: str | Callable[[float], str] | None = None) -> Callable[[float], str]:
    if callable(fmt):
        return fmt
    if isinstance(fmt, str):
        return lambda v: fmt.format(v)
    d = 0
    for t in tick_values:
        s = f"{t:.6f}".rstrip("0").rstrip(".")
        if "." in s:
            d = max(d, len(s.split(".")[1]))
    d = min(d, 3)
    return lambda v: "0" if (signed and abs(v) < 1e-12) else fmt_num(v, d, unit, signed)


def check_percent(values: Iterable[float | None], unit: str, unit_given: bool) -> None:
    """Warn when the default percent unit meets values that look like fractions."""
    vals = [v for v in values if v is not None]
    if unit == "%" and not unit_given and vals and max(abs(v) for v in vals) <= 1 and any(v != 0 for v in vals) \
            and not all(float(v).is_integer() for v in vals):
        warnings.warn("vellum: values are treated as percents by default and these all look like fractions (<= 1). "
                      "Pass percents (37 for 37%) or unit='' for plain numbers.", stacklevel=3)
