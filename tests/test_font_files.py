"""Saving closes the vendored font files (issue #5). An SVG embeds the fonts cut down to its characters and a PDF
embeds static instances of those cuts, so both read the font files. The PDF renders through Chromium."""
from __future__ import annotations

import gc
import warnings

import pytest

import viz as vl
from viz import render


@pytest.mark.parametrize("ext", ["svg", "pdf"])
def test_saving_closes_the_font_files(ext, tmp_path):
    render._cut.cache_clear()  # cached cuts and instances read no file, so this save makes its own
    render._static.cache_clear()
    gc.collect()  # earlier tests' leftovers are freed before recording starts
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", ResourceWarning)
        vl.bars({"A": 1, "B": 2}, title="t").save(tmp_path / f"f.{ext}")
        gc.collect()  # an unclosed font sits in a reference cycle, so it is freed (and warns) only when collected
    assert render._cut.cache_info().misses  # the save read a font file
    unclosed = [str(w.message) for w in caught if issubclass(w.category, ResourceWarning) and ".ttf" in str(w.message)]
    assert not unclosed
