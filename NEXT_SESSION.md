# Next Session: M2 continued — extract-intent + extraction improvements

## What happened this session (2026-04-17)

Built the M2 extract-contracts skill. Three artifacts: `skills/extract-contracts/SKILL.md`, `extract.py`, and `compare.py`.

### Extraction results (dateutil parser module, gpt-oss-20B)

- **78/91 elements** extracted successfully (85.7%)
- **13 failures**: all connection drops from vLLM server on larger prompts (class-level nodes with extensive source code)
- **77/91 parser elements** have populated contracts with `status: needs_review`
- Enriched spec validates against schema with minor warnings only

### Key debugging story: greploom `text` field

The first extraction run produced plausible-looking contracts but comparison against hand-crafted examples revealed the `parserinfo` class was completely hallucinated. Root cause: greploom returns source code in the `text` field, not `source`. The script was reading the wrong field, so the LLM had **zero source code** for all 91 elements and was guessing from function names + training data.

After fixing: parserinfo description went from wrong ("stores year, month, day...") to correct ("language-specific token mappings and parsing rules"). `_parse` invariants went from 0/2 to 2/2 covered.

### Comparison against 7 hand-crafted gold-standard contracts

| Metric | Run 1 (no source) | Run 3 (all fixes) |
|--------|-------------------|--------------------|
| Field coverage | 86% | **93%** |
| Keyword overlap | 22% | **27%** |
| `parse` error severity | `[recoverable]` only | **`[fatal, recoverable]` MATCH** |
| `_parse` invariants | 0/2 | **2/2** |
| parserinfo purpose | Hallucinated | **Correct** |

### Known gaps (not fixable in M2 extraction)

1. **CVE-2022-31688 not captured**: The CVE is not in veripak data or sanicode findings — it was human domain knowledge in the hand-crafted example. Flagged for M3 human review.
2. **vLLM connection drops on large prompts**: ~15% failure rate on elements with large source code. The server drops connections after ~120s of generation. Retry with backoff helps but doesn't fully solve it.
3. **Invariants often too generic**: LLM says "input is not modified" when the hand-crafted version says "token processing is single-pass, left to right." Improving this requires either few-shot examples in the prompt or a separate invariant-extraction pass.
4. **Module-level contracts are weak**: Modules have minimal source code in greploom (just imports), so the LLM can't infer much about the module's role.

### Design decisions captured

- **Element grouping**: Classes with ≤6 methods extracted together; larger classes split into individual calls (prevents vLLM timeouts)
- **In-place spec update**: Contracts written directly to spec.json, not a separate file
- **Security findings**: Suffix-matched by file path; ecosystem CVEs from veripak also injected into prompts
- **Model name auto-resolution**: Script queries `/v1/models` to get the exact model ID (vLLM rejects "default")

## What's next

### Prerequisites (do these first)

1. **Rebuild CPGs with treeloom 0.9.0+ and `--include-source`** (#35). The dateutil CPG was built with treeloom 0.7.0, which doesn't honor `--include-source` — all 8,039 nodes have zero source text. The installed treeloom is 0.7.0 despite M1 notes saying "rebuilt with 0.9.0." Upgrade treeloom, rebuild both dateutil and jsoup CPGs, rebuild greploom indexes. Then re-run extract-contracts to measure quality with source-populated CPGs.

2. **Verify LLM endpoints are still responding.** The mcp-rhoai cluster sandbox may have been recycled. Quick check: `curl -s <endpoint>/v1/models`.

### Remaining M2 work

1. **extract-intent** — business rules, domain logic, state lifecycle, the "why" behind structures. Per the roadmap, this is the second M2 skill.

2. **Multi-model comparison** — Run extract-contracts on the same elements with granite-8B and ministral-14B. Compare quality across models. We have the infrastructure (`compare.py`) and endpoints ready.

3. **Extraction quality improvements**:
   - Add few-shot examples to the system prompt (use hand-crafted contracts as exemplars)
   - Consider a two-pass approach: extract basic contract first, then a refinement pass for invariants and trust boundaries
   - Handle module-level elements differently (aggregate info from child elements)

4. **vLLM timeout mitigation** (#34):
   - Try the gpt-oss-20b replica endpoint for load balancing
   - Truncate greploom context to a token budget (e.g. 6000 tokens)
   - Consider using the 8B model for large elements (faster generation)
   - Check OpenShift route timeout annotations

### Open issues from this session

| Issue | Repo | What |
|-------|------|------|
| #33 | code-translation-skills | Unit tests for extract.py and compare.py |
| #34 | code-translation-skills | vLLM connection drops investigation |
| #35 | code-translation-skills | Rebuild CPGs with treeloom 0.9.0+ |
| rdwj/greploom#30 | rdwj/greploom | Query JSON field naming improvement |

### Available LLM endpoints (mcp-rhoai cluster)

Same as last session — all confirmed responding as of 2026-04-17.

| Model | Endpoint |
|-------|----------|
| RedHatAI/granite-3.3-8b-instruct (8B) | `https://granite-3-3-8b-instruct-granite-model.apps.cluster-n7pd5.n7pd5.sandbox5167.opentlc.com` |
| RedHatAI/gpt-oss-20b (20B) | `https://gpt-oss-20b-gpt-oss-model.apps.cluster-n7pd5.n7pd5.sandbox5167.opentlc.com` |
| RedHatAI/gpt-oss-20b replica (20B) | `https://gpt-oss-20b-2-gpt-oss-model-2.apps.cluster-n7pd5.n7pd5.sandbox5167.opentlc.com` |
| mistralai/Ministral-3-14B-Instruct-2512 (14B) | `https://ministral-3-14b-instruct-mistral-model.apps.cluster-n7pd5.n7pd5.sandbox5167.opentlc.com` |

### Reference files

- `skills/extract-contracts/SKILL.md` — skill definition
- `skills/extract-contracts/extract.py` — extraction script
- `skills/extract-contracts/compare.py` — comparison tool
- `spec-schema/examples/dateutil-parser.spec.json` — hand-crafted gold standard
- `dateutil-example/spec.json` — enriched spec from this session (77 contracts populated)
- `dateutil-example/spec.json.skeleton` — backup of M1 skeleton
- `planning/code-translation-kit/roadmap.md` — M2 section
