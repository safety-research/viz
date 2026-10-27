"""The shared renderer at exit (issue #6): a script that saved a figure removes the renderer's temporary directory
itself, before the directory's finalizer would, with a ResourceWarning. Runs headless Chromium in a child Python."""
from __future__ import annotations

import os
import subprocess
import sys


def test_exit_removes_the_temporary_directory_without_a_warning(tmp_path):
    tmp = tmp_path / "tmp"  # the child's temporary directories land here, apart from other processes'
    tmp.mkdir()
    code = "import sys, viz; viz.bars({'A': 1, 'B': 2}, title='t').save(sys.argv[1])"
    r = subprocess.run([sys.executable, "-W", "always::ResourceWarning", "-c", code, str(tmp_path / "f.png")],
                       env=dict(os.environ, TMPDIR=str(tmp)), capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, r.stderr
    assert (tmp_path / "f.png").stat().st_size > 1000
    assert "TemporaryDirectory" not in r.stderr, r.stderr  # "Implicitly cleaning up <TemporaryDirectory ...>"
    assert not list(tmp.glob("viz-*"))
