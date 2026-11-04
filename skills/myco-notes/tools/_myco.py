"""Shared helpers for the Myco Notes tools. Standard library only; the same code runs on Linux, macOS and Windows."""
import os
import re
import subprocess
import sys

IS_WINDOWS = os.name == "nt"


def utf8_console():
    """Make printing safe on consoles that are not UTF-8 (Windows)."""
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def git(*args, cwd=None, input=None):
    """Run git, capture UTF-8 output. Returns the CompletedProcess (never raises on a non-zero exit)."""
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace", input=input)


def toplevel(start):
    """Root of the git repository that contains `start`, or None."""
    r = git("-C", start, "rev-parse", "--show-toplevel")
    return r.stdout.strip() if r.returncode == 0 and r.stdout.strip() else None


def load_conf(root):
    """Read .myco-notes.conf (shell-style KEY=value, quoted values may span lines). No shell is executed."""
    p = os.path.join(root, ".myco-notes.conf")
    conf = {}
    if not os.path.isfile(p):
        return conf
    with open(p, encoding="utf-8") as fh:
        text = fh.read()
    pat = re.compile(r"^[ \t]*([A-Za-z_][A-Za-z0-9_]*)=", re.M)
    n, pos = len(text), 0
    while True:
        m = pat.search(text, pos)
        if not m:
            break
        j = m.end()
        if j < n and text[j] in "\"'":
            q, k, buf = text[j], j + 1, []
            while k < n and text[k] != q:
                if q == '"' and text[k] == "\\" and k + 1 < n and text[k + 1] in '"\\$`':
                    buf.append(text[k + 1])
                    k += 2
                    continue
                buf.append(text[k])
                k += 1
            val, pos = "".join(buf), k + 1
        else:
            e = text.find("\n", j)
            e = n if e < 0 else e
            val, pos = re.split(r"\s+#", text[j:e])[0].strip(), e
        conf[m.group(1)] = val
    return conf


def run_shell(cmd, cwd, timeout=None):
    """Run a command line from the configuration: bash on Linux and macOS, the platform shell (cmd.exe) on Windows."""
    args = cmd if IS_WINDOWS else ["bash", "-c", cmd]
    return subprocess.run(args, cwd=cwd, shell=IS_WINDOWS, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)


def human_size(nbytes):
    for unit in ("B", "K", "M", "G", "T"):
        if nbytes < 1024 or unit == "T":
            return f"{nbytes:.0f}{unit}" if unit == "B" else f"{nbytes:.1f}{unit}"
        nbytes /= 1024
