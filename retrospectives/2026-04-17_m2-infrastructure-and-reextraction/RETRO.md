# Retrospective: M2 Infrastructure Upgrade and Re-extraction

**Date:** 2026-04-17
**Effort:** Upgrade treeloom/greploom, rebuild CPGs with source text, re-extract contracts, add resume support
**Commits:** a39aeab (PR #36, squash merged)
**Issues:** #34 (vLLM drops), #35 (CPG rebuild — closed)

## What We Set Out To Do

From NEXT_SESSION.md, five items:

1. Rebuild CPGs with treeloom 0.9.0+ and `--include-source` (prerequisite)
2. Verify LLM endpoints still responding (prerequisite)
3. Re-run extract-contracts to measure quality with source-populated CPGs
4. Build extract-intent (M2 second skill)
5. Multi-model comparison and extraction quality improvements

## What Changed

| Change | Type | Rationale |
|--------|------|-----------|
| greploom upgraded 0.4.0 → 0.5.0 (mid-session user input) | Scope addition | Fixes were available; rebuilt indexes with new version |
| Skeleton spec expanded from 91 to 372 elements | Good pivot | CPG rebuild with 0.9.0 required re-running discover; scoping to `src/` produced full library, not just parser module. Extraction still scoped to parser. |
| Built `--skip-existing` and incremental save for extract.py | Scope addition | vLLM drops made single-run extraction impractical; resume support turned 4 partial runs into 100% coverage |
| Model spot-check (gpt-oss-20B vs granite-8B) | Good pivot | Confirmed gpt-oss-20B as primary model with evidence instead of assumption |
| extract-intent deferred | Scope deferral | Infrastructure + re-extraction + resume feature consumed the session |
| Multi-model comparison deferred | Scope deferral | Spot-check answered the key question (model ranking); full comparison can wait |
| CLAUDE.md created | Scope addition | Project lacked onboarding context for future agent sessions |

## What Went Well

- **Countermeasure from prior retros worked.** The "inspect actual tool output" pattern caught `attrs.source_text` immediately — one quick check, not a blind run. Compare to M2 session 1 where the wrong field went undetected through 91 extractions.
- **`--skip-existing` paid for itself in the same session.** Four runs: 13 → 73 → 87 → 90 → 91/91. Without it, each vLLM drop would have wasted all prior work.
- **Spot-check methodology was efficient.** Three elements, two models, side-by-side comparison against gold standard. Answered the model question in ~10 minutes instead of a full multi-model run.
- **All 4 LLM endpoints survived the sandbox lifecycle.** No cluster rebuilds needed.
- **Incremental saves proved their value.** The terminal-worker agent reported "0 contracts persisted" but checking the spec directly showed 13 saved — the incremental save worked even when the process was killed.

## Gaps Identified

| Gap | Severity | Resolution |
|-----|----------|------------|
| Field coverage dropped 93% → 86% vs gold standard after CPG rebuild | Investigate | May be due to changed element IDs affecting gold-standard mapping, or richer source context changing LLM output character. Not clearly a regression — extraction rate went 86% → 100%. |
| LLM severity calibration still off ("fatal" vs gold's "recoverable") | Follow-up | Consistent across both models. Likely needs few-shot examples or post-processing normalization. |
| No test suite for extract.py or compare.py | Follow-up | Issue #33 still open. |
| vLLM drops still ~15% per run | Accept | `--skip-existing` makes this manageable. Issue #34 tracks root cause. |

## Action Items

- [ ] Merge to main — done (PR #36)
- [ ] Build extract-intent in next session
- [ ] Investigate field coverage drop (93% → 86%) — is it a real regression or measurement artifact?

## Patterns

**Countermeasure confirmed:** "Inspect actual tool output before writing code that consumes it" — applied successfully this session when checking `attrs.source_text` field location. Three prior instances of this pattern; first time the countermeasure caught it early.

**Start:** When a feature (like `--skip-existing`) emerges from a pain point during the session, build it immediately rather than working around it manually. The resume feature saved more time in-session than it cost to build.

**Continue:** Spot-checking with targeted comparisons (3 elements, 2 models) instead of exhaustive runs. Gets to a decision faster.

**Continue:** Incremental saves for any process that talks to unreliable external services.
