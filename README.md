# Living Notes

A method, a starter tree and a small set of tools for keeping a project's knowledge **accurate, secure, versioned and connected**, for engineers who run large or long projects (infrastructure, platforms, data and ML systems, research, hardware) alone, in teams, or together with AI coding agents.

It started as the operational memory of a long-running, AI-operated engineering project, where the notes had to work for an operator that forgets everything between sessions. If the notes are good enough for that operator, they are good enough for a new teammate, an auditor, or you next year.

## What you get

| Part | What it is |
|---|---|
| `docs/METHODOLOGY.md` | The full method: principles, file roles, entry formats, how to capture information, when to update, relations between files and datasets, git versioning, security, freshness, procedures, working with AI agents, anti-patterns. |
| `template/` | A ready starter tree: entry point (`AGENTS.md` / `CLAUDE.md`), working agreement, master record, runbook with a lessons list, sync tracker (derived-copy ledger, dependency matrix, pending list, sync log), backlog, verification guide, artifact and archive folders, `.gitignore`, config. |
| `tools/notes-commit` | One command to commit with a described message: syntax checks, optional AI co-author trailer, optional sync of executed files, optional mirror push, optional milestone tag. |
| `tools/hooks/pre-commit` | Refuses commits whose added lines look like secrets (versioned; activated with `core.hooksPath`). |
| `tools/notes-lint.py` | Finds missing references, duplicate heading numbers, stale "last updated" headers, passed follow-up dates, incomplete ledger rows and secrets. |
| `tools/build-notes-map.py` | Builds a static, searchable map: notes grouped by purpose, **who mentions whom**, backlinks, per-note git history, recent commits. Refuses to build if a note contains a secret. |
| `tools/mirror-push.sh`, `tools/restore-drill.sh` | A second copy of the repository, and proof that it can be restored. |
| `tools/bootstrap.sh` | Creates a new notes repository from the template in one command. |
| `SKILL.md` | The same method packaged as an agent skill (capture, audit, bootstrap, merge, review). |

## Quick start

```bash
git clone https://github.com/LuzianMe/living-notes.git
cd living-notes
tools/bootstrap.sh ~/projects/my-project-notes --name "My Project" --owner "Your Name" --tz "UTC"
cd ~/projects/my-project-notes
# edit notes/working-agreement.md and notes/state.md, then:
tools/notes-commit "Describe the first real change and why"
python3 tools/notes-lint.py
python3 tools/build-notes-map.py && xdg-open notes-map/index.html
```

Requirements: bash, git, python 3.8+, rsync (for the mirror). The notes map is nicer with `pip install markdown` but works without it.

## Using it with an AI agent

Put the notes repository where the agent works and point it at `AGENTS.md` (Claude Code reads `CLAUDE.md`, which contains `@AGENTS.md`). The entry point lists the read order and the five rules that must never be missed. To use it as a Claude Code skill, copy `SKILL.md` (with `docs/`, `template/`, `tools/`) into a skill folder such as `~/.claude/skills/living-notes/`. Other agents can read `SKILL.md` as a plain procedure.

## The ideas in six lines

1. One source of truth; current state and history are separate; everything is dated in one time zone.
2. Evidence, not conclusions: exact commands, ids, numbers, the undo, the lesson.
3. Relations are explicit: canonical home per fact, references by file name, a dependency matrix, a ledger of derived copies.
4. Git is the history (no `.bak` files); small, described, frequent commits.
5. No secrets in the tree, enforced by a hook, a publication gate and a periodic scan; copies are checksummed, mirrored, snapshotted and restore-drilled.
6. Honest status words: "not verified", "NOT synced", "pending". Never mark something done that is not.

## Tests

```bash
tests/smoke.sh
```
Bootstraps a tree in a temporary folder and exercises commit, hook, lint, map, mirror and restore drill.

## License

See `LICENSE`.
