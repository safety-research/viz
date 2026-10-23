#!/usr/bin/env bash
# Install vellum onto this machine:
#   - put the `vellum` command on PATH (uv tool install --editable); the skill finds this clone,
#     wherever it lives, with `vellum path`
#   - symlink the vellum skill (claude/skills/vellum) into ~/.claude/skills/
#   - install Playwright's headless Chromium, which renders PNG and PDF
#
# The clone IS the installation: the command and the skill link both point back into it, so an
# edit lands in git and `git pull` updates everything. Re-running is safe.
#   VELLUM_NO_TOOL=1      skip the command
#   VELLUM_NO_BROWSER=1   skip the Chromium step
#   CLAUDE_CONFIG_DIR     link into this Claude Code config dir instead of ~/.claude
set -euo pipefail
VELLUM_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_SRC="$VELLUM_DIR/claude/skills/vellum"
SKILLS_DIR="${CLAUDE_CONFIG_DIR:-$HOME/.claude}/skills"
LINK="$SKILLS_DIR/vellum"

# `ln -s` happily links a nonexistent target, which would put a broken skill in front of every
# session. Piped from curl, $0 is "bash" and VELLUM_DIR becomes the caller's cwd, so check first.
if [[ ! -f "$SKILL_SRC/SKILL.md" || ! -f "$VELLUM_DIR/src/vellum/__init__.py" ]]; then
    echo "install.sh: $VELLUM_DIR is not a vellum clone. Run the install.sh inside one." >&2
    exit 1
fi

mkdir -p "$SKILLS_DIR"
# Anything there that is not a link is a separate copy of the skill. Replace it only when it
# matches the repo's, so edits made to the copy are never lost.
if [[ -e "$LINK" && ! -L "$LINK" ]]; then
    if [[ -d "$LINK" ]] && diff -rq "$LINK" "$SKILL_SRC" >/dev/null; then
        rm -r "$LINK"
    else
        echo "install.sh: $LINK is a separate copy of the skill and differs from the repo's." >&2
        echo "  See what differs:  diff -r $LINK $SKILL_SRC" >&2
        echo "  Merge any edits you want to keep into $SKILL_SRC, move $LINK aside, and re-run." >&2
        exit 1
    fi
fi
# -n: on a re-run, plain -sf would follow the existing link to the directory and put a new link
# inside the repo (claude/skills/vellum/vellum). -n replaces the link itself.
ln -sfn "$SKILL_SRC" "$LINK"
echo "Linked the vellum skill: $LINK -> $SKILL_SRC"

if [[ -z "${VELLUM_NO_TOOL:-}" || -z "${VELLUM_NO_BROWSER:-}" ]] && ! command -v uv >/dev/null 2>&1; then
    echo "install.sh: uv not found. Install it: curl -LsSf https://astral.sh/uv/install.sh | sh" >&2
    exit 1
fi

if [[ -z "${VELLUM_NO_TOOL:-}" ]]; then
    uv tool install --quiet --force --editable "$VELLUM_DIR"
    BIN="$(uv tool dir --bin)"
    echo "Installed the vellum command: $BIN/vellum"
    case ":$PATH:" in
        *":$BIN:"*) ;;
        *) echo "Note: $BIN is not on your PATH; add it so the skill can run vellum:  export PATH=\"$BIN:\$PATH\"" ;;
    esac
fi

if [[ -z "${VELLUM_NO_BROWSER:-}" ]]; then
    uv run --project "$VELLUM_DIR" playwright install chromium-headless-shell
    if [[ -z "${VELLUM_NO_TOOL:-}" ]]; then
        "$(uv tool dir --bin)/vellum" setup  # the command's own environment may pin a different Playwright
    fi
    echo "Installed headless Chromium for PNG and PDF"
fi
