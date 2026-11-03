#!/bin/bash
# Smoke test: bootstrap a tree in a temporary folder and exercise the tools. Exit 0 = all passed.
set -u
kit="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT
pass=0; fail=0
ok()   { echo "  PASS $1"; pass=$((pass+1)); }
bad()  { echo "  FAIL $1"; fail=$((fail+1)); }
chk()  { if eval "$2" >/dev/null 2>&1; then ok "$1"; else bad "$1"; fi; }
export GIT_AUTHOR_NAME=Test GIT_AUTHOR_EMAIL=t@example.com GIT_COMMITTER_NAME=Test GIT_COMMITTER_EMAIL=t@example.com

echo "plugin manifests"
chk "plugin.json is valid JSON"         "python3 -c \"import json;json.load(open('$kit/.claude-plugin/plugin.json'))\""
chk "marketplace.json is valid JSON"    "python3 -c \"import json;json.load(open('$kit/.claude-plugin/marketplace.json'))\""
chk "plugin and marketplace names match" "python3 - <<PY
import json
a=json.load(open('$kit/.claude-plugin/plugin.json'));b=json.load(open('$kit/.claude-plugin/marketplace.json'))
assert a['name']==b['plugins'][0]['name'] and 'version' in a and b['plugins'][0]['source'] in ('./', '.')
PY"
chk "skill file has matching name"      "head -5 $kit/skills/living-notes/SKILL.md | grep -q '^name: living-notes'"
chk "marketplace source resolves to the plugin root" "[ -f $kit/.claude-plugin/plugin.json ] && [ -d $kit/skills/living-notes ]"

echo "bootstrap"
"$kit/tools/bootstrap.sh" "$tmp/proj" --name "Demo" --owner "Tester" --tz "UTC" >/dev/null 2>&1
cd "$tmp/proj" || exit 1
chk "baseline commit exists"            "git log --oneline | grep -q Baseline"
chk "placeholders filled"               "! grep -rq '{{' AGENTS.md notes .living-notes.conf"
chk "hooks path is versioned"           "[ \"\$(git config core.hooksPath)\" = tools/hooks ]"
chk "bootstrap.sh not copied into tree" "[ ! -e tools/bootstrap.sh ]"

echo "notes-commit"
echo "- **$(date +%F) (test change):** added a thing, tested, undo: revert." >> notes/state.md
chk "commit with message"               "tools/notes-commit 'Record the test change and why' | grep -q 'Record the test change'"
chk "clean tree says nothing to commit" "tools/notes-commit 'again' | grep -q 'nothing to commit'"
printf '#!/bin/bash\nif then\n' > notes/scripts/broken.sh
chk "syntax error blocks the commit"    "! tools/notes-commit 'broken script'"
rm notes/scripts/broken.sh

echo "pre-commit hook"
printf 'api_key = AbCdEfGhIjKlMnOpQrStUvWx12\n' > notes/secret-test.md
chk "secret is refused"                 "! tools/notes-commit 'add a secret'"
git reset -q; rm -f notes/secret-test.md
printf -- '-----BEGIN RSA PRIVATE KEY-----\nabc\n' > notes/key-test.md
chk "private key block is refused"      "! tools/notes-commit 'add a key'"
git reset -q; rm -f notes/key-test.md
chk "tree is clean again"               "[ -z \"\$(git status --porcelain)\" ]"

echo "lint"
tools/notes-lint.py >/tmp/lint.$$ 2>&1; rc=$?
chk "lint runs on a fresh tree (exit 0 or 1)" "[ $rc -le 1 ]"
printf '\n## 3. One\n## 3. Two\nSee `missing-note.md`. Pending, review-by 2020-01-01.\n' >> notes/runbook.md
tools/notes-lint.py >/tmp/lint.$$ 2>&1; rc=$?
chk "lint finds duplicate heading"      "grep -q 'duplicate heading number 3' /tmp/lint.$$"
chk "lint finds missing reference"      "grep -q 'missing note' /tmp/lint.$$"
chk "lint finds passed follow-up date"  "grep -q 'has passed' /tmp/lint.$$"
git checkout -q -- notes/runbook.md
rm -f /tmp/lint.$$

echo "map"
chk "map builds"                        "python3 tools/build-notes-map.py && [ -f notes-map/index.html ]"
chk "page has history"                  "grep -q 'History' notes-map/p/notes-state.html"
chk "map is gitignored"                 "git check-ignore -q notes-map"
printf 'token = ABCDEFGHIJKLMNOPQRSTUVWXYZ123456\n' > notes/leak.md
chk "map refuses a secret"              "! python3 tools/build-notes-map.py"
rm -f notes/leak.md

echo "mirror and restore drill"
sed -i "s|^MIRROR_TARGET=.*|MIRROR_TARGET=\"$tmp/mirror\"|" .living-notes.conf
git add -A; git commit -q -m "Configure mirror"
chk "mirror push"                       "tools/mirror-push.sh | grep -q 'mirror: pushed'"
chk "mirror contains .git"              "[ -d $tmp/mirror/.git ]"
chk "restore drill passes"              "tools/restore-drill.sh $tmp/mirror | grep -q 'fsck: OK'"

echo; echo "passed $pass, failed $fail"; [ "$fail" = 0 ]
