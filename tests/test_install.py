"""Installing: the skill is where `npx skills add` looks, the wheel carries the templates and docs, and `viz path`
finds them in a checkout and in an installed copy alike."""
from __future__ import annotations

import re
import subprocess
import sys
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "viz" / "SKILL.md"


def test_skill_is_in_the_skills_cli_layout():
    front = SKILL.read_text().split("---")[1]
    assert re.search(r"^name: viz$", front, re.M) and re.search(r"^description: ", front, re.M)
    assert not (ROOT / "skill").exists() and not (ROOT / "install.sh").exists()


def test_skill_names_the_real_install_and_run_commands():
    text = SKILL.read_text()
    assert "uv tool install git+https://github.com/safety-research/viz" in text
    assert "viz run " in text and "install.sh" not in text


def test_viz_path_prints_this_checkout(capsys):
    from viz.cli import main
    assert main(["path"]) == 0
    assert Path(capsys.readouterr().out.strip()) == ROOT


def test_viz_path_falls_back_to_the_package(monkeypatch, tmp_path):
    from viz import cli
    pkg = tmp_path / "site-packages" / "viz"
    pkg.mkdir(parents=True)
    monkeypatch.setattr(cli, "__file__", str(pkg / "cli.py"))
    assert cli.checkout() is None and cli.home() == pkg


def test_viz_run_uses_this_python(tmp_path):
    script = tmp_path / "s.py"
    script.write_text("import sys, viz; print(sys.executable, *sys.argv[1:])\n")
    r = subprocess.run([sys.executable, "-m", "viz.cli", "run", str(script), "a", "--b"], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    assert r.stdout.split() == [sys.executable, "a", "--b"]


def test_wheel_ships_the_templates_and_docs(tmp_path):
    subprocess.run(["uv", "build", "--quiet", "--wheel", "--out-dir", str(tmp_path), str(ROOT)], check=True)
    names = set(zipfile.ZipFile(next(tmp_path.glob("viz-*.whl"))).namelist())
    for f in ["viz/examples/01_hbar.py", "viz/examples/README.md", "viz/docs/guide.md", "viz/docs/reference.md",
              "viz/docs/gallery/01_hbar.png", "viz/cli.py", "viz/fonts"]:
        assert any(n == f or n.startswith(f + "/") for n in names), f
