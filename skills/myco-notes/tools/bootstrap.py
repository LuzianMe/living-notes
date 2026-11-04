#!/usr/bin/env python3
"""bootstrap: create a new notes repository from the Myco Notes template.

  tools/bootstrap <target-dir> --name "Project name" [--owner "Name"] [--tz "MST (UTC-7)"] [--no-commit]

Copies template/ into <target-dir>, fills the {{PLACEHOLDERS}}, copies tools/ and docs/*.md, makes git use the versioned hooks
(core.hooksPath = tools/hooks), and makes the baseline commit. The target must be empty or not exist.
"""
import argparse
import datetime
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
KIT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import _myco  # noqa: E402

NOT_COPIED = {"bootstrap", "bootstrap.cmd", "bootstrap.py", "__pycache__"}


def main():
    _myco.utf8_console()
    ap = argparse.ArgumentParser(prog="bootstrap", add_help=True)
    ap.add_argument("target")
    ap.add_argument("--name", required=True)
    ap.add_argument("--owner", default=None)
    ap.add_argument("--tz", default="UTC")
    ap.add_argument("--no-commit", action="store_true")
    a = ap.parse_args()
    owner = a.owner or _myco.git("config", "user.name").stdout.strip() or "owner"

    target = os.path.abspath(a.target)
    if os.path.exists(target) and os.listdir(target):
        print(f"bootstrap: {target} exists and is not empty", file=sys.stderr)
        return 1
    os.makedirs(target, exist_ok=True)

    shutil.copytree(os.path.join(KIT, "template"), target, dirs_exist_ok=True)
    shutil.copytree(HERE, os.path.join(target, "tools"), dirs_exist_ok=True, ignore=lambda d, names: [n for n in names if n in NOT_COPIED])
    docs = os.path.join(KIT, "docs")
    os.makedirs(os.path.join(target, "docs"), exist_ok=True)
    if os.path.isdir(docs):
        for f in os.listdir(docs):
            if f.endswith(".md"):
                shutil.copy2(os.path.join(docs, f), os.path.join(target, "docs", f))

    subs = (("{{PROJECT_NAME}}", a.name), ("{{OWNER}}", owner), ("{{TIMEZONE}}", a.tz), ("{{DATE}}", datetime.date.today().isoformat()))
    for dp, dn, fn in os.walk(target):
        dn[:] = [d for d in dn if d != ".git"]
        for f in fn:
            if f.endswith(".md") or f == ".myco-notes.conf":
                p = os.path.join(dp, f)
                with open(p, encoding="utf-8", newline="") as fh:
                    s = fh.read()
                for k, v in subs:
                    s = s.replace(k, v)
                with open(p, "w", encoding="utf-8", newline="") as fh:
                    fh.write(s)

    if not _myco.IS_WINDOWS:
        for d in ("tools", os.path.join("tools", "hooks")):
            full = os.path.join(target, d)
            for f in os.listdir(full):
                p = os.path.join(full, f)
                if os.path.isfile(p):
                    os.chmod(p, os.stat(p).st_mode | 0o111)

    if _myco.git("-C", target, "init", "-q", "-b", "main").returncode != 0:  # git older than 2.28
        _myco.git("-C", target, "init", "-q")
        _myco.git("-C", target, "symbolic-ref", "HEAD", "refs/heads/main")
    _myco.git("-C", target, "config", "core.hooksPath", "tools/hooks")
    print(f"bootstrap: created {target}")
    if not a.no_commit:
        _myco.git("-C", target, "add", "-A")
        r = subprocess.run(["git", "-C", target, "commit", "-q", "-m", "Baseline: notes tree created from the Myco Notes template"], capture_output=True, text=True, encoding="utf-8", errors="replace")
        if r.returncode:
            print(f"bootstrap: baseline commit failed ({r.stderr.strip()}); set git user.name and user.email, then commit", file=sys.stderr)
        else:
            print(_myco.git("-C", target, "log", "--oneline", "-1").stdout.strip())
    print("""
Next steps:
  1. Edit notes/working-agreement.md and notes/state.md (headline facts, components).
  2. Set MIRROR_TARGET in .myco-notes.conf and run tools/mirror-push (then a timer every few hours).
  3. Set up an independent encrypted snapshot of the mirror and run tools/restore-drill once.
  4. python3 tools/build-notes-map.py   (navigable map with backlinks and history)
  5. Commit after every meaningful update:  tools/notes-commit "what changed and why"
  6. Sharing with a team (GitHub or GitHub Enterprise): see docs/TEAM.md; teammates run tools/setup-clone after cloning.
  (On Windows in cmd or PowerShell write tools\\notes-commit; in Git Bash, WSL, macOS and Linux write tools/notes-commit.)""")
    return 0


if __name__ == "__main__":
    sys.exit(main())
