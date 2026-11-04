#!/usr/bin/env python3
"""Cross-platform test (Linux, macOS, Windows) that needs no bash: copies ONLY the skill folder to a temporary place, then
bootstraps a notes tree from that copy and exercises the real launchers (the .cmd files on Windows). Exit 0 = all passed."""
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL = os.path.join(REPO, "skills", "myco-notes")
WIN = os.name == "nt"
passed = failed = 0

os.environ.update(GIT_AUTHOR_NAME="Test", GIT_AUTHOR_EMAIL="t@example.com", GIT_COMMITTER_NAME="Test", GIT_COMMITTER_EMAIL="t@example.com")


def check(name, ok, detail=""):
    global passed, failed
    if ok:
        passed += 1
        print(f"  PASS {name}")
    else:
        failed += 1
        print(f"  FAIL {name}" + (f"\n       {detail}" if detail else ""))


def run(cmd, cwd, stdin=None):
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace", input=stdin)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def git(cwd, *a):
    return run(["git", *a], cwd)


def main():
    tmp = tempfile.mkdtemp(prefix="myco-native-")
    try:
        kit = os.path.join(tmp, "skill-only")
        shutil.copytree(SKILL, kit, ignore=shutil.ignore_patterns("__pycache__"))

        def L(root, name):  # the launcher a user would type
            p = os.path.join(root, "tools", name)
            return [p + ".cmd"] if WIN else [p]

        proj = os.path.join(tmp, "proj")
        print("bootstrap (from the copied skill folder only)")
        rc, out = run(L(kit, "bootstrap") + [proj, "--name", "Demo", "--owner", "Tester", "--tz", "UTC"], tmp)
        check("bootstrap runs", rc == 0, out)
        check("baseline commit exists", "Baseline" in git(proj, "log", "--oneline")[1])
        check("placeholders filled", all("{{" not in open(os.path.join(proj, f), encoding="utf-8").read() for f in ("AGENTS.md", ".myco-notes.conf")))
        check("hooks path is versioned", git(proj, "config", "core.hooksPath")[1].strip() == "tools/hooks")
        check("bootstrap launcher not copied", not os.path.exists(os.path.join(proj, "tools", "bootstrap.py")))
        check("team files present", all(os.path.exists(os.path.join(proj, p)) for p in (".github/workflows/notes-check.yml", "docs/TEAM.md", ".gitattributes")))

        print("notes-commit")
        with open(os.path.join(proj, "notes", "state.md"), "a", encoding="utf-8") as fh:
            fh.write("\n- native test change\n")
        rc, out = run(L(proj, "notes-commit") + ["Record the native test change and why"], proj)
        check("commit with message", rc == 0 and "Record the native test change" in out, out)
        rc, out = run(L(proj, "notes-commit") + ["again"], proj)
        check("clean tree says nothing to commit", "nothing to commit" in out, out)
        bad = os.path.join(proj, "notes", "scripts", "broken.py")
        with open(bad, "w", encoding="utf-8") as fh:
            fh.write("def (:\n")
        rc, out = run(L(proj, "notes-commit") + ["broken script"], proj)
        check("syntax error blocks the commit", rc != 0, out)
        os.remove(bad)
        git(proj, "reset", "-q")

        print("pre-commit hook (run by git through its own sh)")
        leak = os.path.join(proj, "notes", "secret-test.md")
        with open(leak, "w", encoding="utf-8") as fh:
            fh.write("api_key = AbCdEfGhIjKlMnOpQrStUvWx12\n")
        rc, out = run(L(proj, "notes-commit") + ["add a secret"], proj)
        check("secret is refused", rc != 0 and "possible secret" in out, out)
        os.remove(leak)
        git(proj, "reset", "-q")
        key = os.path.join(proj, "notes", "key-test.md")
        with open(key, "w", encoding="utf-8") as fh:
            fh.write("-----BEGIN RSA PRIVATE KEY-----\nabc\n")
        rc, out = run(L(proj, "notes-commit") + ["add a key"], proj)
        check("private key block is refused", rc != 0, out)
        os.remove(key)
        git(proj, "reset", "-q")
        check("tree is clean again", git(proj, "status", "--porcelain")[1].strip() == "")

        print("lint and map")
        rc, out = run([sys.executable, os.path.join(proj, "tools", "notes-lint.py")], proj)
        check("lint runs", rc in (0, 1) and "notes-lint:" in out, out)
        rc, out = run([sys.executable, os.path.join(proj, "tools", "build-notes-map.py")], proj)
        check("map builds", rc == 0 and os.path.exists(os.path.join(proj, "notes-map", "index.html")), out)

        print("mirror and restore drill")
        mirror = os.path.join(tmp, "mirror")
        conf = os.path.join(proj, ".myco-notes.conf")
        with open(conf, encoding="utf-8") as fh:
            text = fh.read()
        text = "".join(f'MIRROR_TARGET="{mirror}"\n' if l.startswith("MIRROR_TARGET=") else l for l in text.splitlines(True))
        with open(conf, "w", encoding="utf-8", newline="") as fh:
            fh.write(text)
        run(L(proj, "notes-commit") + ["Configure mirror"], proj)
        rc, out = run(L(proj, "mirror-push"), proj)
        check("mirror push to a local directory", rc == 0 and "mirror: pushed" in out and os.path.isdir(os.path.join(mirror, ".git")), out)
        rc, out = run(L(proj, "restore-drill") + [mirror], proj)
        check("restore drill passes", rc == 0 and "fsck: OK" in out, out)
        arch = os.path.join(tmp, "backup.zip")
        with zipfile.ZipFile(arch, "w") as z:
            for dp, _dn, fn in os.walk(mirror):
                for f in fn:
                    full = os.path.join(dp, f)
                    z.write(full, os.path.relpath(full, mirror))
        rc, out = run(L(proj, "restore-drill") + [arch], proj)
        check("restore drill from a zip archive", rc == 0 and "fsck: OK" in out, out)
        bare = os.path.join(tmp, "mirror.git")
        git(tmp, "init", "-q", "--bare", bare)
        text = "".join(f'MIRROR_TARGET="git:{bare}"\n' if l.startswith("MIRROR_TARGET=") else l for l in text.splitlines(True))
        with open(conf, "w", encoding="utf-8", newline="") as fh:
            fh.write(text)
        git(proj, "commit", "-qam", "git mirror target")
        rc, out = run(L(proj, "mirror-push"), proj)
        check("mirror push to a git remote (git:URL)", rc == 0 and "main" in git(bare, "branch", "--list")[1], out)

        print("team setup")
        clone = os.path.join(tmp, "clone")
        git(tmp, "clone", "-q", proj, clone)
        check("hooks path is not cloned", git(clone, "config", "core.hooksPath")[1].strip() == "")
        rc, out = run(L(clone, "setup-clone"), clone)
        check("setup-clone activates the hook in a fresh clone", rc == 0 and git(clone, "config", "core.hooksPath")[1].strip() == "tools/hooks", out)
        base = git(proj, "rev-parse", "HEAD")[1].strip()
        with open(os.path.join(proj, "notes", "plans", "backlog.md"), "a", encoding="utf-8") as fh:
            fh.write("- team test line\n")
        rc, out = run(L(proj, "notes-commit") + ["--branch", "feat-a", "Team test change and why"], proj)
        check("notes-commit --branch creates the branch", rc == 0 and git(proj, "symbolic-ref", "--short", "HEAD")[1].strip() == "feat-a", out)
        rc, out = run(L(proj, "ci-check") + [base], proj)
        check("ci-check passes on a clean change", rc == 0 and "ci-check: passed" in out, out)
        with open(os.path.join(proj, "notes", "leak2.md"), "w", encoding="utf-8") as fh:
            fh.write("api_key = AbCdEfGhIjKlMnOpQrStUvWx12\n")
        git(proj, "switch", "-q", "-c", "feat-leak")
        git(proj, "add", "-A")
        git(proj, "commit", "-q", "--no-verify", "-m", "bypass the hook")
        rc, out = run(L(proj, "ci-check") + [base], proj)
        check("ci-check catches a secret committed with --no-verify", rc != 0 and "FAIL" in out, out)
        git(proj, "switch", "-q", "main")
        remote = os.path.join(tmp, "remote.git")
        git(tmp, "init", "-q", "--bare", remote)
        git(proj, "remote", "add", "origin", remote)
        with open(os.path.join(proj, "notes", "plans", "backlog.md"), "a", encoding="utf-8") as fh:
            fh.write("- push test line\n")
        rc, out = run(L(proj, "notes-commit") + ["--branch", "feat-b", "--push", "Push test and why"], proj)
        check("notes-commit --push publishes the branch", "feat-b" in git(tmp, "ls-remote", "--heads", remote)[1], out)

        print("direct python call")
        rc, out = run([sys.executable, os.path.join(proj, "tools", "notes_commit.py"), "--help"], proj)
        check("python tools/notes_commit.py --help", rc == 0 and "--branch" in out, out)
    finally:
        def _force(func, path, _exc):
            os.chmod(path, 0o700)
            func(path)
        shutil.rmtree(tmp, onerror=_force)
    print(f"\npassed {passed}, failed {failed}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
