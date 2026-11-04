# Living Notes for a team (GitHub, GitHub Enterprise and similar)

The notes tree is a git repository, so a team shares it like code. This page is the set-up and the working routine. The reasons are in `METHODOLOGY.md` section 18.

## 1. One-time set-up (about 15 minutes)
1. **Create a private repository** on your hosting service (notes hold operational detail; keep them private) and push the notes tree to it:
   ```bash
   git remote add origin <url-of-the-new-repository>
   git push -u origin main
   ```
2. **Check that the workflow runs.** The tree already contains `.github/workflows/notes-check.yml`. Open a throw-away pull request and see the `notes-check` job pass. On GitHub Enterprise Server, change `runs-on:` to a runner label your instance has, and make sure `actions/checkout` is available there (mirror it or allow it).
3. **Protect `main`** (Settings, Branches, add a rule for `main`):
   - require a pull request before merging, with at least 1 approval;
   - require status checks to pass, and select `notes-check`;
   - require review from Code Owners (after step 4);
   - block force pushes; optionally require linear history.
4. **Name the reviewers.** Edit `.github/CODEOWNERS` (users or teams) and remove the leading `#` on the lines you want. Keep the working agreement and `tools/` under the maintainers.
5. **Tell everyone the routine** (section 2). Point AI agents at `AGENTS.md`; it already says to work on a branch.

## 2. The routine for every contributor
```bash
git clone <url> && cd <repo>
tools/setup-clone                       # once per clone: activates the secret-refusing hook
git pull --ff-only                      # start from the latest main
# ... change the notes (verify against the live system first; read each file just before editing) ...
python3 tools/notes-lint.py             # fix errors
tools/notes-commit --branch short-name --pr "what changed and why"
```
`--branch` creates the branch, `--pr` pushes it and opens the pull request with the GitHub CLI (`gh`); without `gh` it tells you the branch to open by hand. The `notes-check` job runs the secret scan and the lint; a maintainer reviews and merges.

An AI agent follows the same routine: it works on a branch and opens the pull request; a human merges.

## 3. Conflicts
Two people often add a line at the top of the sync log or a row to the changelog at the same time. Resolve by **keeping both sides**, keep the newest-first order, re-run `python3 tools/notes-lint.py`, commit. Small pull requests merged the same day avoid most of it. Do not resolve a conflict by regenerating a whole file.

## 4. Secrets
The hook is a safety net on each clone; CI is the control. If CI reports a possible secret: remove it from the change, **rewrite the branch so the value is gone from every commit** (not just the last one), and treat the value as exposed: rotate it at its source. Never put the value in the pull request text or a comment.

## 5. Reading and writing without a clone
Possible through the hosting API or an integration that edits files in the repository (reading is safe; a one-line fix is fine). It skips the hook, the lint and the commit helper and makes a multi-file update many commits, so prefer a clone, a branch and a pull request. Agents that run in the cloud normally clone the repository anyway.

## 6. GitHub Enterprise notes
- Everything above is plain git plus one workflow file; nothing depends on github.com.
- Claude Code plugin from your own server: copy this kit into a repository on your instance and add it with its git URL (`/plugin marketplace add https://<your-host>/<org>/living-notes.git`).
- Codex and other agents: link or copy `skills/living-notes/` into the agent's skills folder (see the main README).
- Mirror and restore drill still apply: the hosting service is one copy, not a backup. Keep an independent snapshot (`tools/mirror-push.sh`, `tools/restore-drill.sh`).

## 7. What CI checks (`tools/ci-check`)
1. Every line the pull request adds is scanned with the same rules as the local hook (`tools/secret-scan`).
2. `tools/notes-lint.py`: errors fail the check; warnings do not, unless you set `CI_LINT_STRICT=1` in `.living-notes.conf`.

Run it locally the same way: `tools/ci-check origin/main`.
