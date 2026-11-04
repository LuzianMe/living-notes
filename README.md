# Living Notes

A method, a starter tree and a small set of tools for keeping a project's knowledge **accurate, secure, versioned and connected**, for engineers who run large or long projects (infrastructure, platforms, data and ML systems, research, hardware) alone, in teams, or together with AI coding agents.

It started as the operational memory of a long-running, AI-operated engineering project, where the notes had to work for an operator that forgets everything between sessions. If the notes are good enough for that operator, they are good enough for a new teammate, an auditor, or you next year.

Agent-neutral: the skill follows the open [Agent Skills](https://agentskills.io/specification) format, so Claude Code, OpenAI Codex and other agents that read `SKILL.md` and `AGENTS.md` can use it. Everything it needs is inside one folder, `skills/living-notes/`.

## What you get (all paths inside `skills/living-notes/`)

| Part | What it is |
|---|---|
| `SKILL.md` | The skill: five working modes (capture, audit, bootstrap, merge, restore/review) plus resume/hand-off, guard rails and an execution-environment check. |
| `docs/METHODOLOGY.md` | The full method: principles, file roles, entry formats, how to capture information, when to update, relations between files and datasets, git versioning, security, freshness, procedures, working with AI agents, anti-patterns. |
| `template/` | A ready starter tree: entry point (`AGENTS.md` / `CLAUDE.md`), working agreement, master record, runbook with a lessons list, sync tracker (derived-copy ledger, dependency matrix, pending list, sync log), backlog, verification guide, artifact and archive folders, `.gitignore`, config. |
| `tools/notes-commit` | One command to commit with a described message: syntax checks, optional AI co-author trailer, optional sync of executed files, optional mirror push, optional milestone tag, and for teams `--branch`, `--push`, `--pr`. |
| `tools/hooks/pre-commit`, `tools/secret-scan` | Refuse commits whose added lines look like secrets (versioned; activated with `core.hooksPath`; the same rules run in CI). |
| `tools/notes-lint.py` | Finds missing references, duplicate heading numbers, stale "last updated" headers, passed follow-up dates, incomplete ledger rows and secrets. |
| `tools/build-notes-map.py` | Builds a static, searchable map: notes grouped by purpose, **who mentions whom**, backlinks, per-note git history, recent commits. Refuses to build if a note contains a secret. |
| `tools/mirror-push`, `tools/restore-drill` | A second copy of the repository, and proof that it can be restored. |
| `tools/bootstrap` | Creates a new notes repository from the template in one command. |
| `tools/ci-check`, `tools/setup-clone`, `docs/TEAM.md`, `template/.github/` | Team use: a pull-request check (secret scan + lint), per-clone setup, CODEOWNERS and PR template, and the step-by-step guide for GitHub or GitHub Enterprise. |

At the repository root: `.claude-plugin/` (Claude Code plugin and marketplace manifests), `tests/smoke.sh`, `examples/`, `LICENSE`, `NOTICE`.

## Install

### Claude Code (one command)
```
/plugin marketplace add LuzianMe/living-notes
/plugin install living-notes@living-notes
```
Then ask Claude to "start a living notes tree for my project", "update the notes", "audit the notes" or "commit the notes".

### OpenAI Codex
Codex reads skills from `~/.agents/skills` (all your projects) or `.agents/skills` inside a repository, and follows symlinks. Clone the kit once and link the skill folder:
```bash
git clone https://github.com/LuzianMe/living-notes.git ~/.agents/living-notes-kit
mkdir -p ~/.agents/skills
ln -s ~/.agents/living-notes-kit/skills/living-notes ~/.agents/skills/living-notes
```
Restart Codex if the skill does not appear, then use the same requests as above. (Written from the Codex documentation; the author has not yet run it under Codex, so please report anything that differs.)

### Other agents
Any agent that supports Agent Skills: copy or link `skills/living-notes/` into its skills folder; the folder is self-contained. Any other agent: clone the repository and tell it to read `skills/living-notes/SKILL.md` as a procedure; once a notes tree exists, point it at the tree's `AGENTS.md`.

### No agent
Use the tools directly (below). The method is plain Markdown plus git.

## Sharing with a team
Put the notes tree in a private repository on GitHub, GitHub Enterprise or any git host. A bootstrapped tree already contains a pull-request check (`.github/workflows/notes-check.yml`), a CODEOWNERS file and a PR template. Teammates run `tools/setup-clone` once after cloning and change notes with `tools/notes-commit --branch NAME --pr "message"`. Set-up, branch protection and conflict handling: `skills/living-notes/docs/TEAM.md`.

## Platform support
Linux, macOS and Windows (native, Git for Windows, or WSL). The tools are Python 3.8+ (standard library only) plus git; each has a launcher for every shell. In Git Bash, WSL, macOS and Linux write `tools/notes-commit ...`; in cmd or PowerShell write `tools\notes-commit ...` (a `.cmd` launcher) or `python tools\notes_commit.py ...`. Remote mirrors over ssh need rsync and ssh; a `git:URL` mirror target needs neither. The kit's tests run on all three systems in GitHub Actions.

## Quick start (without an agent)

```bash
git clone https://github.com/LuzianMe/living-notes.git
cd living-notes/skills/living-notes
tools/bootstrap ~/projects/my-project-notes --name "My Project" --owner "Your Name" --tz "UTC"
cd ~/projects/my-project-notes
# edit notes/working-agreement.md and notes/state.md, then:
tools/notes-commit "Describe the first real change and why"
python3 tools/notes-lint.py
python3 tools/build-notes-map.py && xdg-open notes-map/index.html
```

The notes map is nicer with `pip install markdown` but works without it.

## Using it with an AI agent

Put the notes repository where the agent works and point it at `AGENTS.md` (Claude Code reads `CLAUDE.md`, which contains `@AGENTS.md`; Codex reads `AGENTS.md` directly). The entry point lists the read order and the rules that must never be missed. The skill finds its own `tools/`, `docs/` and `template/` next to `SKILL.md`, so no environment variable or install path is needed.

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
Runs automatically on Linux and macOS for every push (GitHub Actions). Checks the plugin manifests and the skill file against the Agent Skills specification, then copies **only** the skill folder to a temporary place and, from that copy, bootstraps a tree and exercises commit, hook, lint, map, mirror and restore drill.

## Contributing

See `AGENTS.md` for the repository layout and the rules for changing the kit.

## License

Apache License 2.0. See `LICENSE` and `NOTICE`.
