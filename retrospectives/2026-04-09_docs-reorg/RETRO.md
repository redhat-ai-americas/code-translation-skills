# Retrospective: docs-reorg

**Date:** 2026-04-09
**Effort:** `/docs-reorg` run splitting project documentation into four sibling top-level directories (`docs/`, `planning/`, `research/`, `retrospectives/`), renaming `docs/references/shared/` to `docs/references/python-migration/`, adding `docs/README.md` + `llms.txt` + `.claude/docs-state.json`, sweeping open issues for moved paths, merging to main via admin rebase.
**PR:** #27 (merged 2026-04-09, admin rebase, 7 commits preserved)
**Issues swept:** #14–#23, #26
**Issues filed as follow-ups:** #28 (CHANGELOG.md + tagged releases), #29 (hosted docs site evaluation)
**Commits:** `d39d65c`, `105b9cf`, `713b879`, `e1817b8`, `bef3608`, `16fafe7`, `2b1e354`

## What We Set Out To Do

Run the `/docs-reorg` skill to clean up a tree where user-facing reference, in-flight planning, internal build history, and research stubs had all accumulated inside `docs/` and at the repo root. Target: a `docs/` directory that an external contributor lands on and sees only shipped reference material, with planning and research in visually distinct sibling directories.

## What Changed

| Change | Type | Rationale |
|---|---|---|
| `docs/references/shared/` renamed to `docs/references/python-migration/` (27 skill `INDEX.md` files touched) | Good pivot, user-driven | My Phase 0 plan was to keep `shared/` in place because of the 27-file touch cost. User reframed around future-proofing — the py2to3 skills will be deprecated, so don't make the next reorg inherit an older decision. Reframe was clearly correct. See Key Finding below. |
| `docs/process/` moved as a coherent cluster to `research/process/` instead of scattered per file semantics | Good judgment call | Inventory sub-agent suggested scattering (BUILD-TRACKER stays, others split between research/ and planning/). Kept whole because REVIEW-PROMPT ↔ REVIEW-REPORT cross-references would fragment; "internal build history" is a cleaner mental model than micro-purpose splitting. Preserved readability post-move. |
| `llms-full.txt` deliberately skipped | Scope deferral (correct) | Project is under active development with 50K+ `PLAN.md` and 174K `MIGRATION-GUIDE.md`. Curated inlined bundle would be large and quickly stale; `llms.txt` already provides solid discoverability. Rationale captured in commit body and state file. |
| No `demos/` directory created | Scope deferral (correct) | Only candidate artifacts (`run-status-*.html`) are gitignored and out of scope. Documented in state file. |
| `GETTING-STARTED.md` kept at root rather than moved into `docs/` | Good judgment call | Well-known quick-start landing convention; 2 README links would have needed updating for marginal cleanup value. |

## What Went Well

- **Phase 0 delegation worked cleanly.** Two parallel Explore sub-agents (inventory + reference graph) ran in one round. The reference-graph sub-agent caught the `../../../docs/references/shared/` pattern in 27 skill `INDEX.md` files that my own grep would have taken multiple rounds to find.
- **Granular commit history preserved through rebase merge.** Seven commits, each with a distinct logical purpose, all landed on main unsquashed via `gh pr merge --admin --rebase`. Honors the linear-history rule set in the prior retro's follow-up. `git log --follow` traces every moved file back to initial commit.
- **Rename detection held at ≥93% on every move.** Most at 100%. No history loss anywhere.
- **Dry-run discipline caught the idempotency bug in the issue sweep regex.** First pass produced `planning/planning/BACKLOG.md` because the backticked rule ran first and the bare rule then fired inside the already-replaced text. Caught before touching GitHub, fixed with negative lookbehind, re-dry-run clean, then applied.
- **Link checker verified zero broken links** across 174 markdown files after each phase and once more at the end. The Python script fits the skill's ~60-line guideline and ignored fenced code blocks as specified.
- **User's ack on the plan was load-bearing.** The Phase 0 report surfaced the `docs/references/shared/` decision explicitly as a hard constraint, which prompted the reframe. The one place I had wrong-framing, the pre-state report is what caught it.

## Key Finding: Framing pushback is the second instance of this pattern

The prior retro flagged "stress-test any proposed framing against the full set of use cases the user has in mind, not just the artifacts visible in the repo" as a Start item. That same pattern surfaced again today: I cited the 27-file touch cost as a reason to keep `docs/references/shared/` in place, framing the decision as cost-benefit of work. User reframed around future-proofing — the old decision's path structure was going to outlive the skills that needed it. The feedback memory `feedback_framing_and_bounding.md` was loaded into my context and I still reached for the cost-counting frame first.

This is not a one-off. It's the same class of error as the naming overfit from the bootstrap retro: anchoring on the most salient artifact in front of me ("touching 27 files feels expensive") instead of asking "what frame does this decision live inside?" ("the files I'm guarding are tied to soon-deprecated skills"). Two instances in two retros makes this a systemic pattern worth naming.

The countermeasure isn't "think harder about framing." It's a concrete habit: **when I'm about to flag something as a hard constraint, explicitly ask "what's the time horizon of the thing I'm protecting?"** A constraint that binds only to already-deprecating artifacts is much weaker than a constraint that binds to shipped doctrine. I didn't check.

## Gaps Identified

| Gap | Severity | Resolution |
|---|---|---|
| Framed `docs/references/shared/` as a hard constraint without asking how long the thing being protected was going to live. Second instance of the framing-anchor pattern. | Recurring | Added to Start items below. Also worth a note back to the framing-and-bounding memory if you want — the countermeasure is specific enough to encode. |
| First pass of issue-sweep regex wasn't idempotent (`BACKLOG.md` → `planning/BACKLOG.md` rule fired inside the already-replaced text). | One-off (process win) | Dry-run caught it, fixed with negative lookbehind, no damage. No action item. |
| The Edit tool's "read before edit" requirement tripped the worker sub-agent three times on files it hadn't Read yet in its own context. | Accept (tool behavior) | Worker adapted correctly each time. Not a project issue. |
| Inventory sub-agent miscounted the `docs/references/shared/` cluster as 12 files when it's actually 11. | Accept (minor stat error) | Caught in my own spot-check before writing `docs/README.md`. Low-stakes. |
| `CHANGELOG.md` missing, no tagged releases yet. | Follow-up | Issue #28 filed. |
| Hosted docs site not yet in place; tree is approaching the size where GitHub markdown rendering stops being the best experience. | Follow-up | Issue #29 filed. |

## Action Items

- [x] Filed #28 (CHANGELOG.md + tagged releases) as a follow-up
- [x] Filed #29 (hosted docs site evaluation) as a follow-up
- [ ] Consider updating `feedback_framing_and_bounding.md` memory with the "time horizon of the thing I'm protecting" countermeasure, since the pattern has now recurred

## Start / Stop / Continue

**Start:**
- When flagging something as a "hard constraint," explicitly name the time horizon of the thing being protected. A constraint tied to soon-deprecated code is weaker than a constraint tied to shipped doctrine. Don't collapse the two.
- Write regex replacement rules idempotently from the start (negative lookbehind on file-reference patterns) rather than relying on ordering.

**Stop:**
- Anchoring on the most visible cost ("27 files to touch") as a reason not to do something, without asking whether the thing protected by the cost is itself going to last.

**Continue:**
- Dry-run every batch external operation (issue edits, script replacements) before applying. The issue-sweep dry-run caught the idempotency bug cleanly.
- Granular commits + rebase merge rather than squash for multi-concern structural work. Future bisect and history spelunking benefit from the per-concern boundaries.
- Pre-state reports with explicit judgment calls surfaced before execution. The Phase 0 report is what surfaced the `docs/references/shared/` decision in a form the user could push back on.
- Parallel sub-agents for investigation phases (inventory + reference graph in one round). Worked well here and saved several rounds of my own Grep calls.
- `git mv` for every move, with post-commit `git log --follow` verification that rename detection held.
