# Retrospective: Vertical Plane Pivot

**Date:** 2026-04-09
**Effort:** Redesign the project's architecture around the "vertical plane" specification model, replacing the old Mode A/B milestone roadmap with a spec-centric approach.
**Issues:** Informed by review of all 8 open issues (#17, #19, #23, #25, #26, #28, #29, #30)
**Commits:** Uncommitted at time of retro; committed as part of this session's closing.

## What We Set Out To Do

Review open issues, assess project state, decide what to work on next.

## What Changed

| Change | Type | Rationale |
|--------|------|-----------|
| "Review issues" became a full design pivot | Good pivot | Milestone discussion surfaced that the old roadmap conflated kit-build phases with universal migration phases; the vertical plane model resolved the confusion |
| Mode A (transform) / Mode B (rewrite) collapsed into one flow | Good pivot | Always produce the spec. Mechanical tools are accelerators within generation, not a separate path |
| Archive/new-repo plan dropped; staying in `code-translation-skills` | Good pivot | User had already decided this; agent was carrying stale assumptions from old planning docs |
| Human-in-the-loop elevated to first-class design concern | Good pivot | User identified this as underexplored; spec metadata model (confidence/source/status/assigned_to) emerged from the discussion |
| `manage-project` skill added (GitHub/GitLab templates, regulated-environment tracking) | Scope addition | User raised auditability requirements |
| Old planning directory renamed and cleaned (3 files removed, 2 rewritten) | Good pivot | Old docs were actively causing drift in other sessions |
| Spec schema deferred to next session | Scope deferral | Design discussion was the priority; schema needs focused, example-driven attention |
| Package name settled: `code-translation-kit` | Decision | Available on PyPI, clean name |

## What Went Well

- The vertical plane model emerged through genuine back-and-forth. User's "two halves separated by a plane" framing, agent's analysis of where it gets hard, user's human-in-the-loop addition — each built on the last.
- Cross-cutting concerns (testing, project tracking, documentation) integrated without adding milestones or disrupting the structure.
- Review sub-agent caught real issues: missing `report-gaps` skill, human-in-the-loop absent from cross-cutting disciplines section, stale README pointer, six wrong milestone references.
- Planning directory cleanup was decisive. Three superseded files removed, directory renamed to match content, no lingering mess.
- `NEXT_SESSION.md` written to help the next session start from the new model rather than rediscovering the old one.

## Gaps Identified

| Gap | Severity | Resolution |
|-----|----------|------------|
| Agent assumed "new repo + archive" was still the plan until user corrected | Pattern instance | Third instance of framing-anchor drift (see Patterns below) |
| Another Claude Code session in parallel kept reverting to old model | Systemic | The old planning docs were literally pulling the other agent back. Cleaning them out was the fix. |
| 8 open issues predate the pivot; may need re-scoping | Follow-up | Review against new milestones |
| #28 (CHANGELOG.md + tagged releases) still open | Follow-up | Do before or during M0 |
| #25 (default merge method) still open | Follow-up | Trivial repo settings change |
| No worked example validating the spec schema | Accept | Explicitly deferred; NEXT_SESSION.md captures approach |

## Action Items

- [x] Commit and push the vertical-plane-pivot changes
- [ ] Next session: define spec schema (M0) using example-driven approach
- [ ] Review 8 open issues against new milestones — close or re-scope stale ones
- [ ] Fix #25 (merge method) — 2-minute repo settings change
- [ ] Start #28 (CHANGELOG.md) before more work lands

## Patterns

**Third instance of framing-anchor drift.** The agent carried the old roadmap's "archive and new repo" assumption into this session without questioning it. The user had to correct: "I thought we already decided to stay with code-translation-skills." Same root class as the naming incident (retro 1) and the docs-reorg anchoring (retro 2).

But this session also surfaced a **stronger manifestation**: a separate Claude Code session, started fresh, kept reverting to the old architecture because the old planning docs were still in the repo. The artifacts themselves were the frame anchor — not just in-context salience, but on-disk presence. Cleaning them out was the structural fix. This is direct evidence for the project's core thesis: you have to actively frame and bound the agent's context, or the old artifacts will pull it back.

**Countermeasure update:** The retro 2 countermeasure ("name the time horizon of the thing being protected") didn't prevent this instance because the anchor wasn't a constraint being defended — it was an assumption being carried. Additional countermeasure: **when a design pivots, immediately clean up or clearly mark superseded artifacts.** Don't leave old plans sitting next to new ones expecting the agent to know which is current. Old artifacts have gravity.

**Start:** Clean up superseded planning artifacts immediately after a pivot, not as a follow-up.
**Stop:** Leaving old and new planning docs coexisting in the same directory.
**Continue:** Using concrete user corrections as data points for the framing-and-bounding thesis (#26). Three retros, three instances, one pattern — this is becoming well-documented evidence.
