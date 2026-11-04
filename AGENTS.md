# Living Notes kit: contributor guide (for people and agents changing this repository)

This repository is a kit, not a notes tree. Do not confuse it with the notes trees it creates (those start from `skills/living-notes/template/`).

## Layout
- `skills/living-notes/` : the whole product, **self-contained** (a skill-only installer delivers just this folder). `SKILL.md`, `tools/`, `docs/METHODOLOGY.md`, `template/`. Nothing in it may refer to files outside the folder or to an environment variable.
- `.claude-plugin/` : Claude Code plugin and marketplace manifests (the plugin root is the repository root).
- `tests/smoke.sh` : the test. Run it before every commit; all checks must pass.
- `examples/` : sample entries for readers.

## Rules
1. **One copy of everything.** Do not duplicate tools or docs for a second agent; add installation instructions instead.
2. **Stay agent-neutral** in `SKILL.md`, `tools/` and `template/`. Agent-specific text belongs in the README or in the manifest folders.
3. **No secrets, no personal data** (hostnames, paths, addresses) in any file or commit; the tests use obviously fake values.
4. **Versions move together:** `.claude-plugin/plugin.json` `version` equals `metadata.version` in `SKILL.md` (the test checks it). Bump both, tag `vX.Y.Z` and make a GitHub release.
5. `SKILL.md` follows the Agent Skills specification (name equals the folder name, description at most 1024 characters, under 500 lines).
6. Tools target bash, git, python 3.8+ and rsync. Keep them working on Linux and macOS; Windows is supported through WSL.
7. Change the method in `docs/METHODOLOGY.md` first, then the tools and template that implement it (section 17 maps one to the other).
