# Retrospective: code-translation-skills bootstrap

**Date:** 2026-04-08
**Effort:** `/project-setup` run that grew into a full handoff of the repo to the `redhat-ai-americas` org: working-tree cleanup, repo transfer, relicense to Apache-2.0, public project board with seeded Done + Backlog items, contributor artifacts, and branch protection.
**Issues:** #5–#13 (Done, from git history), #14–#23 (Backlog, contributor-ready)
**Commits:** `4e05f08`, `c7a6a02`, `f1ccb4c`, `75ffd83`, `410522a`

## What We Set Out To Do

Bootstrap GitHub project tracking and standard repo artifacts (LICENSE, CONTRIBUTING, SECURITY, etc.) for `code-translation-skills` via the `/project-setup` skill. The initial scope was a board and some files.

## What Changed

| Change | Type | Rationale |
|---|---|---|
| Added repo transfer `rdwj → redhat-ai-americas` | Scope expansion (correct) | User surfaced the "invite contributors" goal mid-session; a personal-account repo was the wrong home for that. Transfer was the right answer. |
| Kept name `code-translation-skills` instead of renaming | Good pivot | Proposed `code-modernization-skills`; user stress-tested with a brand-new Java → Rust port example and the framing collapsed. See "Key finding" below. |
| MIT → Apache-2.0, added NOTICE file, copyright line on LICENSE | Scope expansion (correct) | Natural consequence of moving to a Red Hat org; flagged in the state report and user added it to the plan. |
| Cleaned working tree with 3 pre-existing WIP commits before transfer | Scope expansion (necessary) | Pre-existing WIP (run status viewer + BACKLOG + agent-kit ideas) had to either ride along or be handled first. Split into three logical commits; gitignored dev-time HTML previews. |
| Seeded 10 contributor-ready Backlog issues from BACKLOG.md | Scope expansion | My "inviting contributors" line in a followup summary was info-only but read as an action item. User asked for concrete issues; they were well-scoped and well-received. |
| Self-approval workflow discussion after `/protect-main` landed | Post-hoc decision | Should have been raised before applying protection, not after. User classified this as a once-per-project concern; noted but not systemic. |

## What Went Well

- **Guardrails held throughout.** No auto-commits of user WIP, no overwrite of LICENSE without explicit approval, explicit confirmation before the repo transfer (the one irreversible step).
- **Clean commit history.** Five commits, conventional format, no spam, proper `Assisted-by` trailer, no `Co-authored-by`.
- **Working-tree cleanup was surgical.** Three commits split by logical concern, gitignore rule for dev previews instead of deleting the user's work.
- **Clarification batching.** Security contact, repo visibility, README URL all bundled into one question turn rather than drip-feeding.
- **Retroactive clarification on "keep this all private"** caught a potentially significant misunderstanding before I started making the repo itself private.
- **Pacing matched the user's appetite.** End-to-end execution once approvals were in place, with milestone updates but no excessive status chatter.

## Key Finding: Naming Overfit as a Microcosm of the Project's Thesis

I proposed renaming `code-translation-skills` → `code-modernization-skills` because the repo I was looking at had a py2to3 heritage. The user pushed back with a Java → Rust greenfield port: a translation with no "legacy" side at all. The proposed name didn't fit.

The root cause wasn't bad reasoning about the name. It was that I had over-indexed on the py2to3 artifacts *in front of me* and let "legacy modernization" silently become a frame for the whole project. That is exactly the failure mode this project exists to solve: **any LLM behind an agent will over-index on what's already in context, and if the task involves an old artifact, the model will default to old-artifact handling pathways — even when the whole point is to do something new with it.**

The fix is deliberate framing and bounding up-front (goals stated in target terms, memories that shape the prior, rules that rule out familiar-but-wrong paths, skills that reinforce the intended workflow). That converts "I see an old thing, therefore the next step is [the old thing's usual handling]" into "Of course I see an old thing — dealing with old things is exactly what we're here for, so let's plan the new thing."

This is worth a dedicated research / exposition document for the project at some point — it directly sells the thesis.

## Gaps Identified

| Gap | Severity | Resolution |
|---|---|---|
| `required_linear_history: true` silently changes merge strategy — future PRs must be squash or rebase, not merge commits. Not surfaced during `/protect-main`. | Follow-up | Action item below: set repo default merge method. |
| Self-approval workflow discussion happened *after* `/protect-main` rather than before. | Accept (one-off) | User flagged as once-per-project; not systemic. |
| `gh api --raw-field` fumbled nested JSON for branch protection; needed a stdin-JSON retry. | Accept | One-round-trip cost; the working pattern is now in the conversation for future reference. |
| "Inviting contributors" phrased as an info-only followup but read as an action item. | Accept | Phrasing drift; worth being more explicit about info-vs-action next time. |
| Naming proposal didn't stress-test against full project scope. | Key finding above | Captured as a memory (`feedback_framing_and_bounding.md`) so the principle applies to future sessions. |

## Action Items

- [ ] **Set the repo's default merge method to Squash or Rebase** (GitHub repo Settings → General → Pull Requests) so contributors don't hit the wrong merge button under the new linear-history rule. Follow-up issue to be created.
- [ ] **Optional**: stub a research doc under `ideas/framing-and-bounding/` (or similar) to capture the thesis-selling insight from this session. User flagged as valuable but not urgent.

## Start / Stop / Continue

First retro in this project — no pattern data yet. Initial notes to revisit next retro:

- **Start:** Stress-testing any proposed framing (names, taxonomies, scopes) against the *full* set of use cases the user has in mind, not just the artifacts visible in the repo.
- **Start:** Surfacing workflow implications of infrastructure changes (like linear history) at the moment they're being decided, not after.
- **Continue:** Explicit confirmation before irreversible actions (repo transfer, relicense, etc.); clean commit splits; batched clarifications.
- **Continue:** Pre-state reports before taking action, so the user can veto specific steps.
