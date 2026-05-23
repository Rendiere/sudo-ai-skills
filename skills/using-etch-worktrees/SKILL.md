---
name: using-etch-worktrees
description: Use whenever new feature/fix/chore work is about to start in the etch repo — phrases like "let's work on", "fix", "implement", "start", "claim", "let's build", any Linear ID reference (etc-XXXX / ETC-XXXX), any bd-XX reference, or any `git checkout -b` / `git worktree add` attempt. Etch-specific gate that enforces the `make worktree` flow, the etc-XXXX-slug naming convention, and the branch-lock rule. Complements (does not replace) `superpowers:using-git-worktrees`.
---

# Using Etch Worktrees

## Purpose

The etch repo runs multiple Claude Code agents in parallel, each on its own branch. Without discipline, stray worktrees accumulate, env-file copies rot after secret rotations, and agents land edits on the wrong branch. This skill is the gate: every new piece of named work happens in a fresh worktree off `origin/dev`, created via `make worktree`, with a Linear-style name.

## When to Use

Trigger on any of:

- User says "let's work on", "fix", "implement", "start", "claim", "let's build", "begin", "tackle".
- User pastes or references a Linear ID (`etc-XXXX`, `ETC-XXXX`) or a beads ID (`bd-XX`).
- Agent is about to run `git checkout -b feat/...`, `git switch -c`, or `git worktree add` by hand.
- Session begins with a clear feature/fix scope in the brief.

Do NOT trigger for: read-only questions, codebase exploration, `bd list`/`bd show`, doc-only edits the user is doing in-place, or work that's already running inside a worktree.

## The Rule

```
feature work in etch ≡ a worktree under .worktrees/<etc-XXXX-slug>/ branched off origin/dev
```

Three sub-rules:

1. **Worktree per scope.** One worktree per Linear issue / bead. Never pile two scopes into one tree.
2. **Linear-ID naming.** `etc-XXXX-slug` (e.g. `etc-433-bid-cta-hide`). Reject bare slugs (`outcome-A`, `cohort-thing`) and propose the correct shape from the issue title.
3. **Branch-lock.** Once inside `.worktrees/<name>/`, never `git checkout`, `git switch`, or `git checkout -b` to another branch. If new work appears, `cd` back to the main repo and create another worktree.

## Flow

### Step 1 — Where am I?

```bash
git worktree list --porcelain | head -20
pwd
```

Decide:

- `pwd` is the etch repo root (`~/dev/personal/sudo/etch` or wherever the main worktree lives): the rule says **create a worktree before writing**. Read-only exploration is fine in place.
- `pwd` is under `.worktrees/<name>/`: rule satisfied — proceed. Confirm the branch matches the work scope (`git branch --show-current`).
- `pwd` is under `.claude/worktrees/<name>/`: an agent harness worktree — same as above, proceed but the branch-lock rule still applies.

### Step 2 — Infer or confirm the name

The convention is `etc-XXXX-slug`. Validate against `^etc-[a-z0-9]+(-[a-z0-9-]+)?$`. Sources, in order of preference:

1. **Linear ID in the user's message.** "Fix etc-433" → `etc-433-<short-slug>` where `<short-slug>` is a 2-4-word kebab summary of the issue title.
2. **Beads task with `linear:ETC-XXX` label.** Pull via `bd show <id>` → look for `LABELS: linear:ETC-XXX` → use `etc-XXX-<slug>`.
3. **No Linear ID at hand.** Kebab the user's brief into 2-4 words, prefix with `etc-` only if the work is Linear-tracked; otherwise use the repo's existing prefix pattern (`feat/<slug>`) via `PREFIX=feat` and a bare slug.

Reject names that don't match the regex. Propose the correct shape, get confirmation, then proceed.

### Step 3 — Auto-create

From the etch repo root (cd back if you're not there):

```bash
make worktree NAME=etc-XXXX-slug
```

(Override the branch prefix with `PREFIX=fix|chore|--no-prefix` when the work isn't a feature.)

The make target:

1. Fetches `origin/dev`.
2. Creates `.worktrees/etc-XXXX-slug/` on branch `feat/etc-XXXX-slug` (or whatever `PREFIX` resolved to) off `origin/dev`.
3. Symlinks `.env.agent`, `.env.dev`, `.env.docker`, `.env.local`, `.env.prd`, `.env.test` from the main worktree.

If the make target is missing on the current checkout (only present from `dev` onward), use the underlying `./scripts/worktree.sh` directly with the same args.

### Step 4 — Switch in and work

```bash
cd .worktrees/etc-XXXX-slug
```

All subsequent tool calls — Edits, Bash, Read, etc. — use absolute paths under `.worktrees/etc-XXXX-slug/` or run with cwd set there. Do not edit files in the main worktree once you're scoped to a feature.

## The Branch-Lock Rule (in detail)

Once `pwd` is under `.worktrees/<name>/`, the worktree is **scoped to its branch for its lifetime**. Forbidden:

```bash
git checkout dev                   # ✗ contaminates the worktree
git switch feat/other-thing        # ✗ same
git checkout -b feat/quick-fix     # ✗ creates a hidden second branch
```

Why: `.beads/`, build artefacts, env-file symlinks, and editor state are all keyed to the branch this tree was cut for. A swap silently breaks every assumption and produces edits that land on the wrong PR.

Allowed inside the worktree:

```bash
git fetch origin                   # ✓ remote-only
git pull --rebase origin dev       # ✓ rebases the worktree's branch
git merge dev                      # ✓ stays on this branch
git push -u origin <branch>        # ✓
```

If new work surfaces mid-flight: finish or stash the current line, `cd` back to the main repo, and `make worktree NAME=<next>`.

## Cleanup expectations

You don't manually clean worktrees up. Two mechanisms do it:

1. **Auto-prune hook** (`.claude/hooks/auto-prune-merged-worktree.sh`) — fires after every successful `gh pr merge`. Removes the matching `.worktrees/<name>/` and deletes the local branch. Refuses on dirty trees, primary branches, or anything outside `.worktrees/`.
2. **Periodic sweep** — `make worktree-clean` (or `make worktree-clean-dry` to preview) removes worktrees whose PR is `MERGED`/`CLOSED` on origin, or whose branch was deleted on origin. Skips dirty trees, open PRs, locked worktrees (unless `--force`), and primary branches. The `landing-the-plane` skill runs this after every successful dev→main release.

You only need to think about cleanup if you see something surprising in `git worktree list` — stray entries, branches you don't recognise. Then run `make worktree-clean-dry` and read the verdict per worktree.

## Etch-specific vs `superpowers:using-git-worktrees`

`superpowers:using-git-worktrees` is the generic worktree-creation skill (any project). This skill is the **etch-specific gate** that demands `make worktree`, the `etc-XXXX-slug` naming, and the branch-lock rule. Use both: this one decides whether a worktree is needed and what to name it; the superpowers one covers underlying mechanics if you ever need them outside etch.

## Related memory

- `feedback_always_worktree_off_dev` — never stash unrelated WIP to reuse the current checkout.
- `feedback_branch_worktree_naming` — branches/worktrees mirror Linear IDs (`etc-XXXX-slug`).

## Reference

- Full conventions: `docs/development/worktrees.md` in the etch repo.
- Underlying script: `scripts/worktree.sh` (create), `scripts/worktree-clean.sh` (sweep).
- Hook source: `.claude/hooks/auto-prune-merged-worktree.sh`.
