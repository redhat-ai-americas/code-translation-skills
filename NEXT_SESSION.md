# Next Session: M2 continued — extract-intent

## What happened this session (2026-04-17, session 2)

### Infrastructure upgrades

- **treeloom**: 0.7.0 → 0.9.0. CPGs now have `source_text` in `attrs` for all functions and classes.
- **greploom**: 0.4.0 → 0.5.0. Rebuilt indexes for both dateutil and jsoup.
- **dateutil CPG**: Rebuilt scoped to `src/`, 8,039 nodes, 355 with source text (all 306 functions + 49 classes).
- **jsoup CPG**: Rebuilt scoped to `src/`, 63,055 nodes, source populated.
- **dateutil spec**: Rebuilt skeleton with new node_refs — now 372 elements (full library, not just parser).

### Extraction results (dateutil parser module, gpt-oss-20B)

- **91/91 elements** extracted successfully (100%) across 4 runs with `--skip-existing`
- **~15% connection drop rate** per run, but resume makes it manageable
- All 4 LLM endpoints still responding on mcp-rhoai cluster

### Model comparison spot-check (isoparse, parserinfo, _parse)

| Dimension | gpt-oss-20B | granite-8B |
|---|---|---|
| Purpose quality | More precise, names specific components | More generic |
| Postconditions | Much more detailed (4 items vs 2) | Sparse |
| JSON reliability | Consistent | Failed once (invalid JSON on _parse) |
| Trust boundary | Correct (out=trusted) | Sometimes wrong (out=untrusted) |
| Error conditions | More granular (4 items vs 1 for isoparse) | Fewer, less specific |

**Decision**: Use gpt-oss-20B as primary model. granite-8B only as fallback for elements that consistently timeout.

### Comparison against gold standard (7 hand-crafted contracts)

| Metric | M2 session 1 (no source) | This session (source populated) |
|---|---|---|
| Field coverage | 93% | 86% |
| Keyword overlap | 27% | 21% |
| `_parse` invariants | 2/2 | 2/2 |
| parserinfo purpose | Correct | Correct |
| Extraction success rate | 85.7% | **100%** |

Coverage numbers dipped slightly but extraction is now complete. The quality difference may be due to changed element IDs affecting which elements map to gold standard, or the richer source context changing the LLM's output character.

### Code changes

- **PR #36**: `--skip-existing` flag + incremental save for extract.py (on `chore/extract-contracts-resume` branch)

## What's next

### Primary: extract-intent (M2 second skill)

Build `skills/extract-intent/` — extracts business rules, domain logic, state lifecycle, and the "why" behind structures. Per the roadmap, this is the second M2 skill.

Key design questions to resolve:
- How does intent differ from contracts? Contracts = observable behavior ("what"); intent = domain knowledge, design rationale ("why")
- What does the output schema look like? Does it go in the spec alongside contracts, or in a separate section?
- Does it need source code (greploom), or is it more about module-level patterns and relationships?
- Should it run per-element like contracts, or per-module/per-class?

### Secondary: extraction quality improvements

1. Add few-shot examples to the system prompt (use hand-crafted contracts as exemplars)
2. Two-pass approach: basic contract first, then refinement pass for invariants
3. Handle module-level elements differently (aggregate info from child elements)
4. Severity calibration: LLM uses "fatal" where gold says "recoverable"

### Remaining M2 items

- Multi-model comparison (granite-8B, ministral-14B) — infrastructure ready, need to run and analyze
- Merge PR #36

### Open issues

| Issue | Repo | What |
|-------|------|------|
| #33 | code-translation-skills | Unit tests for extract.py and compare.py |
| #34 | code-translation-skills | vLLM connection drops investigation |
| #35 | code-translation-skills | Rebuild CPGs with treeloom 0.9.0+ (DONE) |
| #36 | code-translation-skills | PR: --skip-existing for resumable extraction |
| rdwj/greploom#30 | rdwj/greploom | Query JSON field naming improvement |

### Available LLM endpoints (mcp-rhoai cluster)

All confirmed responding as of 2026-04-17.

| Model | Endpoint |
|-------|----------|
| RedHatAI/granite-3.3-8b-instruct (8B) | `https://granite-3-3-8b-instruct-granite-model.apps.cluster-n7pd5.n7pd5.sandbox5167.opentlc.com` |
| RedHatAI/gpt-oss-20b (20B) | `https://gpt-oss-20b-gpt-oss-model.apps.cluster-n7pd5.n7pd5.sandbox5167.opentlc.com` |
| RedHatAI/gpt-oss-20b replica (20B) | `https://gpt-oss-20b-2-gpt-oss-model-2.apps.cluster-n7pd5.n7pd5.sandbox5167.opentlc.com` |
| mistralai/Ministral-3-14B-Instruct-2512 (14B) | `https://ministral-3-14b-instruct-mistral-model.apps.cluster-n7pd5.n7pd5.sandbox5167.opentlc.com` |

### Tool versions

- treeloom: 0.9.0
- greploom: 0.5.0

### Reference files

- `skills/extract-contracts/SKILL.md` — skill definition
- `skills/extract-contracts/extract.py` — extraction script (with --skip-existing)
- `skills/extract-contracts/compare.py` — comparison tool
- `spec-schema/examples/dateutil-parser.spec.json` — hand-crafted gold standard
- `dateutil-example/spec.json` — enriched spec (91/91 parser contracts, gpt-oss-20b)
- `planning/code-translation-kit/roadmap.md` — M2 section
