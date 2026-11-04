#!/usr/bin/env python3
"""notes-lint: cheap consistency checks for a Living Notes tree (Python standard library only).

Checks
  refs      backticked names of notes (*.md) and of repository paths that do not exist
  headings  duplicate numbered headings in one file ("## 9." twice)
  fresh     "Last updated <date>" header older than the newest changelog entry in the same file
  due       follow-up dates that have passed ("after 2026-11-04", "review-by 2026-12-01") on lines not marked DONE (heuristic; words: after, about, due, review-by, waiting until, on or after)
  ledger    sync-tracker rows without a last-synced date or a refresh method
  secrets   secret-looking strings (same patterns as the pre-commit hook)
  orphans   notes that no other note mentions by file name (info only)

Usage:  tools/notes-lint.py [--root DIR] [--quiet] [--strict]
Exit:   0 clean, 1 warnings, 2 errors (secrets). --strict turns warnings into exit 1 even for info-only runs of 'due'.
Ignore: put regular expressions (one per line) in .living-notes-lint-ignore; a finding whose text matches is dropped.
"""
import argparse, datetime, os, re, subprocess, sys

SKIP_DIRS = {".git", "site", "notes-map", "node_modules", "__pycache__"}
SECRET_PATTERNS = [
    r"BEGIN [A-Z ]*PRIVATE KEY",
    r"AKIA[0-9A-Z]{16}",
    r"ghp_[A-Za-z0-9]{30,}",
    r"github_pat_[A-Za-z0-9_]{30,}",
    r"xox[baprs]-[A-Za-z0-9-]{10,}",
    r"sk-[A-Za-z0-9]{32,}",
    r"(?i)(password|passwd|passphrase|secret|token|api[_-]?key|psk)[\"']?\s*[:=]\s*[\"']?[A-Za-z0-9+/_=-]{20,}",
]
DATE = r"\d{4}-\d{2}-\d{2}"


def repo_root(start):
    try:
        return subprocess.run(["git", "-C", start, "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=True).stdout.strip()
    except Exception:
        return os.path.abspath(start)


def read_conf(root):
    conf = {}
    p = os.path.join(root, ".living-notes.conf")
    if os.path.exists(p):
        for line in open(p, encoding="utf-8"):
            m = re.match(r'^\s*([A-Z_]+)=("?)(.*?)\2\s*(#.*)?$', line)
            if m:
                conf[m.group(1)] = m.group(3)
    return conf


def walk_md(root):
    out = []
    for dp, dn, fn in os.walk(root):
        dn[:] = sorted(d for d in dn if d not in SKIP_DIRS)
        for f in sorted(fn):
            if f.endswith(".md"):
                out.append(os.path.relpath(os.path.join(dp, f), root))
    return out


def all_files(root):
    names, paths = set(), set()
    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in dn if d not in SKIP_DIRS]
        for f in fn:
            names.add(f)
            paths.add(os.path.relpath(os.path.join(dp, f), root))
    return names, paths


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=".")
    ap.add_argument("--quiet", action="store_true", help="hide info lines")
    ap.add_argument("--strict", action="store_true")
    a = ap.parse_args()
    root = repo_root(a.root)
    conf = read_conf(root)
    ignore = []
    ip = os.path.join(root, ".living-notes-lint-ignore")
    if os.path.exists(ip):
        ignore = [re.compile(l.strip()) for l in open(ip, encoding="utf-8") if l.strip() and not l.startswith("#")]
    today = datetime.date.today()
    md_files = walk_md(root)
    names, paths = all_files(root)
    top_dirs = {p.split("/")[0] for p in paths if "/" in p}
    findings = []   # (level, file, line, text)

    def add(level, f, line, text):
        s = f"{f}:{line} {text}"
        if any(r.search(s) for r in ignore):
            return
        findings.append((level, f, line, text))

    texts = {}
    mentions = {f: 0 for f in md_files}
    for rel in md_files:
        texts[rel] = open(os.path.join(root, rel), encoding="utf-8", errors="replace").read()

    for rel, text in texts.items():
        lines = text.split("\n")
        in_code = False
        # refs, due, secrets, headings
        seen_heads = {}
        for i, line in enumerate(lines, 1):
            if line.strip().startswith("```"):
                in_code = not in_code
                continue
            for pat in SECRET_PATTERNS:
                if re.search(pat, line):
                    add("ERROR", rel, i, "secret-looking string (remove it or store it where the notes say secrets live)")
                    break
            if in_code:
                continue
            for tok in re.findall(r"`([^`\n]+)`", line):
                tok = tok.lstrip("@")
                if any(c in tok for c in " *<>{}$|()[]") or tok.startswith(("/", "~", "http", "./", "../", ".")):
                    continue
                if rel.startswith(("docs/", "template/")):
                    continue                      # method documentation and templates use illustrative names
                if tok.endswith(".md"):
                    base = os.path.basename(tok)
                    ok = (tok in paths or os.path.normpath(os.path.join(os.path.dirname(rel), tok)) in paths
                          or (base == tok and base in names))
                    if ok:
                        for other in md_files:
                            if os.path.basename(other) == base and other != rel:
                                mentions[other] += 1
                    else:
                        add("WARN", rel, i, f"reference to missing note `{tok}`")
                elif "/" in tok and tok.split("/")[0] in top_dirs and re.search(r"\.[A-Za-z0-9]{1,5}$", tok):
                    if tok not in paths and os.path.normpath(os.path.join(os.path.dirname(rel), tok)) not in paths:
                        add("WARN", rel, i, f"reference to missing file `{tok}`")
            if re.match(r"^\s*(- \*\*|\d+\.\s+\*\*)\s*\d{4}-\d{2}-\d{2}", line) or "DONE" in line or "~~" in line:
                pass
            else:
                for m in re.finditer(rf"\b(after|about|due|review-by|waiting until|on or after)\s+({DATE})\b", line):
                    try:
                        d = datetime.date.fromisoformat(m.group(2))
                    except ValueError:
                        continue
                    if d < today:
                        add("WARN", rel, i, f"follow-up date {m.group(2)} has passed ({m.group(1)}); re-check or mark DONE")
            hm = re.match(r"^(#{1,6})\s+(\d+(?:\.\d+)*)[.)]?\s", line)
            if hm:
                key = (len(hm.group(1)), hm.group(2))
                if key in seen_heads:
                    add("WARN", rel, i, f"duplicate heading number {hm.group(2)} (first at line {seen_heads[key]})")
                else:
                    seen_heads[key] = i
        # fresh
        head = "\n".join(lines[:12])
        hm = re.search(rf"Last updated\s+({DATE})", head)
        if hm:
            cl = re.search(r"^#{1,3}\s+.*changelog.*$", text, re.M | re.I)
            entries = [e for e in re.findall(rf"^- \*\*({DATE})", text[cl.end():] if cl else "", re.M) if e <= (today + datetime.timedelta(days=1)).isoformat()]
            if entries and max(entries) > hm.group(1):
                add("WARN", rel, 1, f"header says last updated {hm.group(1)} but the changelog has entries up to {max(entries)}")

    # ledger completeness
    for rel in md_files:
        if os.path.basename(rel) != "sync-tracker.md":
            continue
        in_table, header = False, []
        for i, line in enumerate(texts[rel].split("\n"), 1):
            if re.match(r"^##\s+Sync targets", line):
                in_table, header = True, []
                continue
            if in_table and line.startswith("## "):
                in_table = False
            if in_table and line.startswith("|"):
                cells = [c.strip() for c in line.strip().strip("|").split("|")]
                if not header:
                    header = [c.lower() for c in cells]
                    continue
                if set("".join(cells)) <= set("-: "):
                    continue
                if len(cells) >= 4:
                    last, how = cells[2], cells[3]
                    if not last or last.startswith("_("):
                        add("WARN", rel, i, f"ledger row '{cells[0]}' has no last-synced date")
                    if not how or how.startswith("_("):
                        add("WARN", rel, i, f"ledger row '{cells[0]}' has no refresh method")
                    if len(cells) >= 5 and re.search(r"pending|behind|stale", cells[4], re.I):
                        add("INFO", rel, i, f"ledger row '{cells[0]}' status: {cells[4][:60]}")

    # orphans (info)
    entry = {"AGENTS.md", "CLAUDE.md", "README.md"}
    for rel in md_files:
        if mentions[rel] == 0 and os.path.basename(rel) not in entry and not rel.startswith(("docs/", "template/")):
            add("INFO", rel, 1, "no other note mentions this file by name")

    order = {"ERROR": 0, "WARN": 1, "INFO": 2}
    findings.sort(key=lambda x: (order[x[0]], x[1], x[2]))
    n = {"ERROR": 0, "WARN": 0, "INFO": 0}
    for lvl, f, ln, text in findings:
        n[lvl] += 1
        if lvl == "INFO" and a.quiet:
            continue
        print(f"{lvl:5} {f}:{ln} {text}")
    print(f"notes-lint: {len(md_files)} notes, {n['ERROR']} errors, {n['WARN']} warnings, {n['INFO']} info")
    if n["ERROR"]:
        return 2
    return 1 if (n["WARN"] or (a.strict and n["INFO"])) else 0


if __name__ == "__main__":
    sys.exit(main())
