#!/bin/bash
# bootstrap.sh: create a new notes repository from the Living Notes template.
#
#   tools/bootstrap.sh <target-dir> --name "Project name" [--owner "Name"] [--tz "MST (UTC-7)"] [--no-commit]
#
# Copies template/ into <target-dir>, fills the {{PLACEHOLDERS}}, copies tools/ and docs/*.md, makes git use the
# versioned hooks (core.hooksPath = tools/hooks), and makes the baseline commit. The target must be empty or not exist.
set -euo pipefail
kit="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
target="${1:-}"; shift || true
name=""; owner="$(git config user.name 2>/dev/null || echo owner)"; tz="UTC"; commit=1
while [ $# -gt 0 ]; do
  case "$1" in
    --name) name="$2"; shift 2;;
    --owner) owner="$2"; shift 2;;
    --tz) tz="$2"; shift 2;;
    --no-commit) commit=0; shift;;
    *) echo "bootstrap: unknown option $1" >&2; exit 2;;
  esac
done
[ -n "$target" ] && [ -n "$name" ] || { sed -n '2,8p' "$0"; exit 2; }
if [ -e "$target" ] && [ -n "$(ls -A "$target" 2>/dev/null)" ]; then echo "bootstrap: $target exists and is not empty" >&2; exit 1; fi
mkdir -p "$target"; target="$(cd "$target" && pwd -P)"
cp -a "$kit/template/." "$target/"
mkdir -p "$target/tools" "$target/docs"
cp -a "$kit/tools/." "$target/tools/"
rm -f "$target/tools/bootstrap.sh"
for d in "$kit"/docs/*.md; do [ -f "$d" ] && cp "$d" "$target/docs/"; done
date_now="$(date +%F)"
find "$target" -type f \( -name '*.md' -o -name '.living-notes.conf' \) -not -path '*/.git/*' -print0 |
  while IFS= read -r -d '' f; do
    NAME="$name" OWNER="$owner" TZ_="$tz" DATE_="$date_now" python3 - "$f" <<'PY'
import os, sys
p = sys.argv[1]; s = open(p, encoding="utf-8").read()
for k, v in (("{{PROJECT_NAME}}", os.environ["NAME"]), ("{{OWNER}}", os.environ["OWNER"]), ("{{TIMEZONE}}", os.environ["TZ_"]), ("{{DATE}}", os.environ["DATE_"])):
    s = s.replace(k, v)
open(p, "w", encoding="utf-8").write(s)
PY
  done
chmod +x "$target/tools/"* "$target/tools/hooks/"* 2>/dev/null || true
cd "$target"
git init -q -b main
git config core.hooksPath tools/hooks
echo "bootstrap: created $target"
if [ "$commit" = 1 ]; then
  git add -A && git commit -q -m "Baseline: notes tree created from the Living Notes template" && git log --oneline -1
fi
cat <<EOF

Next steps:
  1. Edit notes/working-agreement.md and notes/state.md (headline facts, components).
  2. Set MIRROR_TARGET in .living-notes.conf and run tools/mirror-push.sh (then a timer every few hours).
  3. Set up an independent encrypted snapshot of the mirror and run tools/restore-drill.sh once.
  4. python3 tools/build-notes-map.py   (navigable map with backlinks and history)
  5. Commit after every meaningful update:  tools/notes-commit "what changed and why"
  6. Sharing with a team (GitHub or GitHub Enterprise): see docs/TEAM.md; teammates run tools/setup-clone after cloning.
EOF
