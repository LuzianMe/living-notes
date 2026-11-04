#!/bin/bash
# mirror-push.sh: keep a second copy of the notes repository (including .git) on another machine or disk.
# Target comes from MIRROR_TARGET in .living-notes.conf (user@host:/path or a local directory). rsync with --delete, so the
# mirror equals the working copy; history safety comes from an independent snapshot job that backs up the mirror.
# Skips quietly (exit 0) when the target is unreachable or not configured, so a timer never nags.
# Run it from a timer (for example every 6 hours) and after notes-commit -p.
set -eo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
root="$(git -C "$here" rev-parse --show-toplevel)"
cd "$root"
[ -f .living-notes.conf ] && . ./.living-notes.conf
: "${MIRROR_TARGET:=}" "${POST_PUSH_CMDS:=}"
[ -n "$MIRROR_TARGET" ] || { echo "mirror: MIRROR_TARGET not set in .living-notes.conf, skipped"; exit 0; }

case "$MIRROR_TARGET" in
  *:*) host="${MIRROR_TARGET%%:*}"
       ssh -o ConnectTimeout=5 -o BatchMode=yes "$host" true 2>/dev/null || { echo "mirror: $host not reachable, skipped"; exit 0; }
       rsync -a --delete -e "ssh -o BatchMode=yes" "$root/" "$MIRROR_TARGET/";;
  *)   mkdir -p "$MIRROR_TARGET"; rsync -a --delete "$root/" "$MIRROR_TARGET/";;
esac

if [ -n "$POST_PUSH_CMDS" ]; then
  while IFS= read -r c; do
    [ -n "$c" ] || continue
    timeout 120 bash -c "$c" 2>&1 | tail -2 || true     # a failing publish never breaks the push
  done <<< "$POST_PUSH_CMDS"
fi
date +%s > "$root/.git/last-mirror-push" 2>/dev/null || true
echo "mirror: pushed $(du -sh "$root" | cut -f1) to $MIRROR_TARGET"
