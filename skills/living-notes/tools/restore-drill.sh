#!/bin/bash
# restore-drill.sh: prove the notes can be restored. Give it a directory that was restored from the mirror or from a snapshot
# (or a .tar/.tar.gz of it). It runs git fsck, shows the last commits, checks the entry point and the tracker, compares the
# newest commit with the live repository, and prints one line ready to paste into the sync log.
#
#   tools/restore-drill.sh /path/to/restored-copy
#   tools/restore-drill.sh /path/to/backup.tar.gz
set -uo pipefail
src="${1:-}"
[ -n "$src" ] || { echo "usage: restore-drill.sh <restored dir | archive>" >&2; exit 2; }
live="$(git -C "$(dirname "${BASH_SOURCE[0]}")" rev-parse --show-toplevel)"
tmp=""
if [ -f "$src" ]; then tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT; tar -xf "$src" -C "$tmp"; src="$tmp"; fi
repo="$(find "$src" -maxdepth 3 -name .git -type d | head -1)"; repo="${repo%/.git}"
[ -n "$repo" ] || { echo "FAIL: no .git found under $src"; exit 1; }
rc=0
echo "restored repository: $repo"
git -C "$repo" fsck --no-progress 2>&1 | grep -v '^dangling' | sed 's/^/  fsck: /'
[ "${PIPESTATUS[0]}" = 0 ] && echo "  fsck: OK" || { echo "  fsck: PROBLEMS"; rc=1; }
echo "  last commits:"; git -C "$repo" log --oneline -5 | sed 's/^/    /'
for f in AGENTS.md CLAUDE.md; do [ -f "$repo/$f" ] && echo "  entry point present: $f"; done
[ -f "$repo/notes/sync-tracker.md" ] && echo "  tracker present" || { echo "  tracker MISSING"; rc=1; }
a="$(git -C "$repo" rev-parse HEAD 2>/dev/null)"; b="$(git -C "$live" rev-parse HEAD 2>/dev/null)"
if [ "$a" = "$b" ]; then echo "  restored HEAD equals live HEAD ($a)"; else echo "  restored HEAD differs from live HEAD (restored ${a:0:8}, live ${b:0:8}): fine for an old snapshot, check the date"; fi
[ "$rc" = 0 ] && res="OK" || res="PROBLEMS"
echo
echo "Sync-log line: - **$(date +%F) ($(date +%H:%M)):** restore drill from $(basename "$1"): fsck and log $res; HEAD ${a:0:8}."
exit "$rc"
