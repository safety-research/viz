#!/usr/bin/env bash
# Install viz onto this machine:
#   - put the `viz` command on PATH (uv tool install --editable); the skill finds this clone,
#     wherever it lives, with `viz path`
#   - symlink the viz skill (skill/) into ~/.claude/skills/viz
#   - install Playwright's headless Chromium, which renders PNG and PDF
#
# The clone IS the installation: the command and the skill link both point back into it, so an
# edit lands in git and `git pull` updates everything. Re-running is safe.
#   VIZ_NO_TOOL=1      skip the command
#   VIZ_NO_BROWSER=1   skip the Chromium step
#   CLAUDE_CONFIG_DIR     link into this Claude Code config dir instead of ~/.claude
set -euo pipefail
VIZ_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_SRC="$VIZ_DIR/skill"
SKILLS_DIR="${CLAUDE_CONFIG_DIR:-$HOME/.claude}/skills"
LINK="$SKILLS_DIR/viz"

# `ln -s` happily links a nonexistent target, which would put a broken skill in front of every
# session. Piped from curl, $0 is "bash" and VIZ_DIR becomes the caller's cwd, so check first.
if [[ ! -f "$SKILL_SRC/SKILL.md" || ! -f "$VIZ_DIR/src/viz/__init__.py" ]]; then
    echo "install.sh: $VIZ_DIR is not a viz clone. Run the install.sh inside one." >&2
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
# inside the repo (skill/skill). -n replaces the link itself.
ln -sfn "$SKILL_SRC" "$LINK"
echo "Linked the viz skill: $LINK -> $SKILL_SRC"
# The skill used to be called vellum: drop that old link if it is one of ours.
OLD="$SKILLS_DIR/vellum"
if [[ -L "$OLD" && "$(readlink "$OLD")" == */claude/skills/vellum ]]; then
    rm "$OLD"
    echo "Removed the old vellum skill link"
fi

if [[ -z "${VIZ_NO_TOOL:-}" || -z "${VIZ_NO_BROWSER:-}" ]] && ! command -v uv >/dev/null 2>&1; then
    echo "install.sh: uv not found. Install it: curl -LsSf https://astral.sh/uv/install.sh | sh" >&2
    exit 1
fi

if [[ -z "${VIZ_NO_TOOL:-}" ]]; then
    uv tool install --quiet --force --editable "$VIZ_DIR"
    BIN="$(uv tool dir --bin)"
    echo "Installed the viz command: $BIN/viz"
    case ":$PATH:" in
        *":$BIN:"*) ;;
        *) echo "Note: $BIN is not on your PATH; add it so the skill can run viz:  export PATH=\"$BIN:\$PATH\"" ;;
    esac
fi

if [[ -z "${VIZ_NO_BROWSER:-}" ]]; then
    uv run --project "$VIZ_DIR" playwright install chromium-headless-shell
    if [[ -z "${VIZ_NO_TOOL:-}" ]]; then
        "$(uv tool dir --bin)/viz" setup  # the command's own environment may pin a different Playwright
    fi
    echo "Installed headless Chromium for PNG and PDF"
fi
