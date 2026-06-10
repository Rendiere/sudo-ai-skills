---
name: backlog-management
description: Use when deciding whether something belongs as a Linear issue, keeping the Linear board readable and under its plan's issue cap, filing a bug in the standing "Operate a healthy site" project, or answering questions about how the WHAT (Linear) relates to the HOW (Compound Engineering plans). Keeps Linear curated, humanized, and readable for non-technical stakeholders.
---

# Backlog Management

## Overview

**One tracker: Linear.** Linear is the system of record for *what* work exists and how it's going — workspace `sudolabsuk`, team **EtchArt** (issue key `ETC`). There is no second tracker for implementation detail; everything that's a work item lives here. Keep Linear readable for a non-technical teammate (Louis): outcomes, not code.

**Linear = the WHAT. Compound Engineering = the HOW.** `/ce-plan` → `/ce-work` → `/ce-compound`. A CE plan (`docs/plans/ETC-XX-slug.md`) is per-task scratch — never a shadow backlog. Linear stays the WHAT.

## Structure

- **Initiative → projects → issues.** Each project has one owner and is *completable* (it can be finished and closed).
- **Issues carry plain-language acceptance criteria** — a teammate who doesn't read code should understand what "done" means.
- **Area / function is a label, never a project** (e.g. `auctions`, `onboarding`, `infra`). Don't spin up a project per area.

## `ETC-XX` is the join key

One ID ties the whole task together:

- the **Linear issue** (`ETC-XX`)
- its **CE plan** — `docs/plans/ETC-XX-slug.md`, in the repo the work is *for* (etch feature → plan in `etch`; framework work → plan in the framework repo)
- its **branch / worktree** — `etc-XX-slug`
- its **`/ce-compound` learnings**

## Humanize Linear text

Run the `humanizer` skill on anything written into Linear, and format it to scan:

- short lead line, then bullets over paragraphs
- plain verbs, few em-dashes
- outcomes a stakeholder cares about, not implementation steps

## Bugs in shipped features

Bugs are the **one case where an issue is always filed** — we want the learning trail.

- File every shipped-feature bug as a real Linear issue in **one standing project**: [Operate a healthy site](https://linear.app/sudolabsuk/project/operate-a-healthy-site-801def1c19ba) (under the active initiative).
- **Never** reopen a finished project; **never** create a new project per bug.
- When the fix ships, add a one-line entry to that project's **"Fix log"** checklist.

Feature / development work is **not** a "bug issue" — it follows the normal Initiative → project → issue flow.

## Closing work (no manual sync)

Every PR that closes a Linear issue MUST carry one of these in its body:

```
Closes ETC-XX
Fixes ETC-XX
Resolves ETC-XX
```

A GitHub Actions auto-advance workflow moves the Linear issue along automatically once that PR merges with passing checks — **no AI in the loop, no manual reconciliation.** That magic line is the entire mechanism; if it's missing, the issue won't advance.

**Two stages — `Staged`, then `Done`:**

- Merge into **`dev`** → the issue moves to **`Staged`**: engineering-complete, on dev, awaiting release.
- Merge the **`dev`→`main`** release → each referenced issue moves to **`Done`** (live in prod) and is tagged **`release: vX.Y.Z`**.

So `Done` always means "a real user can use it", and the `release:` label batches everything that shipped in one version. `Staged` sits in Linear's *Completed* group (it reads as finished) but stays distinct from live. Adding the `Staged` state is a one-time Team → Workflow settings change — it can't be created via the API.

**The reference is mandatory, enforced by CI.** A `linear-ref-check` job fails any dev PR whose body has no `Closes/Fixes/Resolves ETC-XX` — unless it carries a `no-linear` label for genuinely untracked mechanical PRs. That gate is what makes the auto-advance reliable instead of dependent on someone remembering. At release time, `scripts/linear-release-reconcile.sh` lists what's `Staged` so the release PR provably references every shipping issue.

- Use the `/close-linear <ETC-XX>` skill to generate a PR with the right `Closes ETC-XX` line, branch, and commit message.
- **Multi-task / release PRs:** include one `Closes ETC-XX` line per Linear issue rolled in.

## Keeping Linear under its issue cap

Linear's Free plan has a hard issue cap. When you approach it, archive completed work — archiving is soft-delete: it drops the issue from the cap but preserves history (un-archive via the Linear UI if needed).

```bash
# 1. Check subscription type & current count
curl -s -X POST https://api.linear.app/graphql \
  -H "Authorization: $LINEAR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query":"query { organization { subscription { type } } team(id: \"TEAM_ID\") { issueCount } }"}'

# 2. Archive all Done + Canceled issues (reversible)
LINEAR_API_KEY=... LINEAR_TEAM_ID=... ./scripts/archive-completed.sh
```

`LINEAR_API_KEY` lives in `.env.agent` (not `.env`) — source it before running the script.

### scripts/archive-completed.sh

```bash
#!/usr/bin/env bash
set -euo pipefail
: "${LINEAR_API_KEY:?need LINEAR_API_KEY}"
: "${LINEAR_TEAM_ID:?need LINEAR_TEAM_ID}"

# Fetch all completed + canceled issue IDs, archive each.
# Exclude `Staged`: it's a completed-TYPE state but the issue is awaiting release,
# not finished — archiving it would drop release-pending work off the board.
query='query($teamId: ID!, $after: String) {
  issues(first: 100, after: $after, filter: {
    team: {id: {eq: $teamId}},
    state: {type: {in: [completed, canceled]}, name: {neq: "Staged"}}
  }) { nodes { id identifier } pageInfo { hasNextPage endCursor } }
}'

after="null"
while :; do
  resp=$(curl -s -X POST https://api.linear.app/graphql \
    -H "Authorization: $LINEAR_API_KEY" \
    -H "Content-Type: application/json" \
    -d "$(jq -cn --arg q "$query" --arg t "$LINEAR_TEAM_ID" --argjson a "$after" \
        '{query:$q, variables:{teamId:$t, after:$a}}')")
  ids=$(echo "$resp" | jq -r '.data.issues.nodes[].id')
  for id in $ids; do
    curl -s -X POST https://api.linear.app/graphql \
      -H "Authorization: $LINEAR_API_KEY" \
      -H "Content-Type: application/json" \
      -d "{\"query\":\"mutation{ issueArchive(id: \\\"$id\\\") { success } }\"}" \
      >/dev/null
    echo "archived $id"
  done
  hasNext=$(echo "$resp" | jq -r '.data.issues.pageInfo.hasNextPage')
  [ "$hasNext" = "true" ] || break
  after=$(echo "$resp" | jq -r '.data.issues.pageInfo.endCursor' | jq -Rs .)
done
```

## Red flags

- **Creating a Linear project per area or per bug** → area is a label; bugs go in *Operate a healthy site*.
- **A CE plan growing into a backlog** → that's the tracker's job. Promote durable work items into Linear issues; the plan stays per-task scratch.
- **A PR that closes work but has no `Closes ETC-XX` line** → the issue won't auto-advance. Add the line before merge.
- **Linear text written in engineer-speak** → run `humanizer`; lead with the outcome.
- **Near the issue cap and creating new issues** → archive Done + Canceled first (`scripts/archive-completed.sh`).

## Quick reference

```bash
# Close work: let the PR do it — magic line in the body, then merge
Closes ETC-XX            # (or Fixes / Resolves)
/close-linear ETC-XX     # generates the PR with that line for you

# Keep Linear under the cap (LINEAR_API_KEY from .env.agent)
LINEAR_API_KEY=... LINEAR_TEAM_ID=... ./scripts/archive-completed.sh

# Filing work
# - feature/dev work → Initiative → project → issue (normal flow)
# - bug in a shipped feature → issue in "Operate a healthy site" + Fix-log entry
# - area/function → a label, never a project
```
