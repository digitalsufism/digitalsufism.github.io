#!/usr/bin/env bash
#
# deploy.sh — render the site from `main` and publish it to the `gh-pages` branch.
#
# Usage:
#   ./deploy.sh                 # render + deploy with an automatic commit message
#   ./deploy.sh "my message"    # render + deploy with a custom commit message
#   ./deploy.sh --no-render     # deploy the existing _site/ without re-rendering
#
# Safe to re-run: if the rebuilt site is identical to what is already on
# gh-pages, it exits without committing or pushing.
#
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO"

RENDER=1
MSG=""
for arg in "$@"; do
  case "$arg" in
    --no-render) RENDER=0 ;;
    *) MSG="$arg" ;;
  esac
done
[ -z "$MSG" ] && MSG="Deploy: rebuild site from main ($(date '+%Y-%m-%d %H:%M'))"

# --- guard: must be on main with a clean tree ------------------------------
BRANCH="$(git rev-parse --abbrev-ref HEAD)"
if [ "$BRANCH" != "main" ]; then
  echo "✗ refusing to deploy: you are on '$BRANCH', not 'main'." >&2
  exit 1
fi
if [ -n "$(git status --porcelain --untracked-files=no)" ]; then
  echo "✗ refusing to deploy: main has uncommitted tracked changes. Commit them first." >&2
  git status --short
  exit 1
fi

# --- 1. render -------------------------------------------------------------
if [ "$RENDER" -eq 1 ]; then
  echo "▶ quarto render"
  quarto render
fi
[ -d "$REPO/_site" ] || { echo "✗ _site/ not found — run a render first." >&2; exit 1; }
touch "$REPO/_site/.nojekyll"   # stop GitHub Pages from running Jekyll

# --- 2. stage the built site on a temporary gh-pages worktree --------------
WORKTREE="$(mktemp -d)"
cleanup() { git worktree remove --force "$WORKTREE" 2>/dev/null || true; }
trap cleanup EXIT

echo "▶ checking out gh-pages into a worktree"
git fetch -q origin gh-pages || true
git worktree add -q "$WORKTREE" gh-pages

(
  cd "$WORKTREE"
  git rm -rqf . 2>/dev/null || true
  rsync -a --exclude='.git' "$REPO/_site/" ./
  git add -A
  if git diff --cached --quiet; then
    echo "✓ no changes — gh-pages already matches the built site. Nothing to deploy."
    exit 0
  fi
  echo "▶ committing and pushing gh-pages"
  git commit -q -m "$MSG"
  git push -q origin gh-pages
  echo "✓ deployed: $(git rev-parse --short HEAD) — $MSG"
)

echo "▶ live at https://digitalsufism.github.io (GitHub Pages may take 1–2 min to propagate)"
