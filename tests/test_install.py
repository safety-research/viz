"""install.sh links the skill into the Claude Code config dir and never clobbers an edited copy."""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skill"


def _install(config: Path) -> subprocess.CompletedProcess:
    env = {**os.environ, "CLAUDE_CONFIG_DIR": str(config), "VIZ_NO_BROWSER": "1", "VIZ_NO_TOOL": "1"}
    return subprocess.run(["bash", str(ROOT / "install.sh")], env=env, capture_output=True, text=True, check=False)


def test_install_links_the_skill_and_reruns(tmp_path):
    link = tmp_path / "skills" / "viz"
    for _ in range(2):  # a re-run replaces the link instead of nesting a new one inside the repo
        r = _install(tmp_path)
        assert r.returncode == 0, r.stderr
        assert link.is_symlink() and link.resolve() == SKILL.resolve()
    assert not (SKILL / "viz").exists()


def test_install_replaces_an_identical_copy_but_keeps_an_edited_one(tmp_path):
    link = tmp_path / "skills" / "viz"
    text = (SKILL / "SKILL.md").read_text()
    link.mkdir(parents=True)
    (link / "SKILL.md").write_text(text)
    assert _install(tmp_path).returncode == 0 and link.is_symlink()

    link.unlink()
    link.mkdir()
    (link / "SKILL.md").write_text(text + "\nA local edit.\n")
    r = _install(tmp_path)
    assert r.returncode == 1 and "differs" in r.stderr
    assert not link.is_symlink() and (link / "SKILL.md").read_text().endswith("A local edit.\n")


def test_viz_path_prints_this_checkout(capsys):
    from viz.cli import main
    assert main(["path"]) == 0
    assert Path(capsys.readouterr().out.strip()) == ROOT
