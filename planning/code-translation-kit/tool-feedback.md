# Foundation Tool Feedback

Observations from running all four tools during the M0 spec schema session (2026-04-09). Each tool was run against real codebases: jsoup (Java, 91 files) and python-dateutil (Python, 17 files). All LLM-powered features used Granite 3.3 8b via local Ollama.

## treeloom 0.4.0

**What worked well:**
- Build is fast: 91 Java files parsed in 0.3s, CPG built in 2.3s
- Call resolution is excellent for Java (85%, 5614/6564 calls resolved)
- Subgraph extraction (`treeloom subgraph --function "clean"`) gives a focused view with 2-hop context
- Edge queries are powerful: `treeloom edges --kind calls --target "^clean$"` finds all callers
- Parameter type annotations are preserved: `dirtyDocument: Document` (position 0)
- Data flow edges trace parameter → call → variable → return cleanly

**Issues / improvement opportunities:**
- Python call resolution is notably lower (34% vs 85% for Java). Dynamic dispatch and duck typing are the likely cause, but this means the spec for Python codebases will have more gaps in the structural layer.
- Edge queries don't include file/line on the source/target nodes (shows `?:?`). The node IDs contain the file path, but having file:line in the edge output would save a round-trip query.
- `treeloom config --set` rejects unknown keys silently — no error, just "Unknown config key: llm.provider". This is fine since treeloom has no LLM integration, but a user trying to configure it might be confused. A hint like "treeloom does not use LLM configuration; see greploom for semantic search" would help.
- `treeloom config --init` creates `.treeloom.yaml` in CWD with no warning. If you're in the wrong directory, this leaves a config file in an unexpected place. We accidentally created one in the code-translation-skills repo root and had to clean it up.
- The node ID format (`function:/absolute/path/to/file.java:58:4:16518`) embeds absolute paths. This makes IDs unstable across machines. For the spec's `node_ref` field, this is workable (the spec is generated per-machine), but it means specs aren't portable without path remapping. Consider a relative-path option for node IDs.

**Spec integration notes:**
- The CPG's node hierarchy (module → class → function) maps directly to the spec's `elements` hierarchy. The `discover` skill can walk the CPG and create stub elements for every node.
- The `contains` edges give parent→child relationships needed for the spec's `parent` field.
- The `calls` edges are the basis for `usage_paths` in the spec.

## greploom (latest)

**What worked well:**
- Semantic queries found the right code: "HTML sanitization and XSS prevention" surfaced `Cleaner`, `clean()`, `Safelist`, `isValid()` — all the security-critical components.
- Graph-aware context expansion: results include not just the hit but callers, parameters, and containing classes. This is exactly what a spec-extraction agent needs.
- Index build is fast (2389 nodes for jsoup, 372 for dateutil).
- The `--tier enhanced` option with Granite embeddings works well for domain-specific queries.

**Issues / improvement opportunities:**
- The JSON output for query results doesn't include the source text or Javadoc/docstrings. The `text` field contains a formatted summary like `"## hit: function clean (...)"` but not the actual source code or documentation. A `--include-source` option that includes the raw source lines would help extraction agents.
- No way to query "show me everything greploom knows about this specific CPG node ID." The query interface is text-based semantic search, but sometimes the agent already knows the node and just wants context expansion. A `--node <node_id>` query mode would complement the text search.
- The embedding model isn't shown in the output. When reviewing results, it's useful to know which model produced the embeddings. A `--show-model` or metadata in the JSON output would help.

**Spec integration notes:**
- Greploom is an extraction-time tool, not a spec artifact. Its output isn't stored in the spec; it's used by extraction agents to find relevant code and then populate the spec.
- The `discover` skill should build the greploom index alongside the CPG so subsequent extraction skills can query it.

## sanicode 0.10.0

**What worked well:**
- Findings are rich: CWE ID, severity, compliance cross-references (OWASP ASVS, NIST 800-53, ASD STIG, PCI DSS), and LLM-generated remediation.
- The output maps directly to the spec schema's `security_findings` format with minimal transformation.
- The knowledge graph stats (nodes, edges, entry points, sinks, sanitizers) are useful metadata for the spec.
- Config via `sanicode config set` with dotted paths is clean and scriptable.
- The three-tier LLM config (fast/analysis/reasoning) allows tuning model usage per task.
- LLM-generated remediation is context-specific ("Modify the 'month' function to include an action when a KeyError occurs") — not generic boilerplate.

**Issues / improvement opportunities:**
- **Java support is missing.** Filed as redhat-ai-americas/code-translation-skills#31. The roadmap notes "use Semgrep until sanicode adds Java."
- Scanning the full dateutil codebase (17 files) timed out after 3+ minutes. Scanning just the `parser/` subdirectory (3 files) completed in ~2 seconds. The bottleneck appears to be LLM calls — each finding triggers analysis and remediation generation via Granite 3.3 8b locally. For large codebases, this will be slow. Consider: batch LLM calls, or offer a `--no-llm` mode that produces findings without LLM-generated remediation (the rule-based findings + compliance mappings are still valuable).
- The `sanicode.toml` config file is created in CWD. When running `sanicode config set` from the wrong directory, the config ends up in an unexpected place. We created one in the code-translation-skills repo root and had to move it. Consider a `--config <path>` flag on `config set` or default to `~/.config/sanicode/config.toml` for global config.
- The `--skip-content-policy` flag was needed to avoid even longer scan times. Document what content policy scanning does and when it's safe to skip.
- CWE-913 findings (lines 223, 1429, 1433, 1440) had empty `cwe_name`, `compliance`, and `remediation` fields. The rule matched, but the enrichment pipeline didn't fill in the details. These findings are from SC050 which seems less mature than SC059/SC062.

**Spec integration notes:**
- Each finding's `file` and `line` can be resolved to a CPG node ID by querying `treeloom query --kind function --file <file> --json` and finding the containing function. The `discover` skill should do this resolution to populate the `node_ref` field.
- The `derived_severity` field (sanicode's adjusted severity after LLM analysis) is more useful than the raw `severity` for the spec. Use `derived_severity` when populating the spec.

## veripak 0.3.1

**What worked well:**
- Package audit is comprehensive: version tracking, CVE inventory (from OSV + NVD), EOL status, and LLM-generated migration recommendations.
- The output maps directly to the spec schema's `ecosystem_dependencies` format.
- Works for both Python (PyPI) and Java (Maven Central) ecosystems.
- The LLM-generated `summary.recommendation` field is actionable: "Immediate action is required. Migration to jsoup 1.21.1 is imperative."
- Cost tracking (`_usage` field) shows token counts and estimated cost per audit.

**Issues / improvement opportunities:**
- The `org.jsoup:jsoup` Maven coordinate format only resolved to version 1.15.4, while the simple `jsoup` name resolved to 1.21.1. The Maven Central API query for coordinates seems to hit a different search endpoint that returns stale data. This matters because the `discover` skill will extract coordinates from `pom.xml`.
- The CVE agent hallucinated a CVE for the Maven coordinate query: CVE-2015-3117 is actually an Adobe Flash vulnerability, not a jsoup vulnerability. Granite 3.3 8b is too small for reliable CVE attribution. Consider: cross-validating CVE IDs against the actual OSV/NVD response before including them, or flagging LLM-sourced CVEs as `confidence: low`.
- When ecosystem is auto-inferred without the `-e` flag, `jsoup` was detected as a Python package (there is a `jsoup` on PyPI, different project). The `-e` flag should probably be required when there's ambiguity, or veripak should warn when a package exists in multiple ecosystems.
- The `eol` field often returns `confidence: low` with `project_status: unknown`. The endoflife.date API doesn't cover most libraries — only major runtimes and frameworks. Consider documenting this limitation or falling back to "last release date" heuristics (e.g., if the last release was 3+ years ago, flag it).
- The interactive `veripak config` wizard doesn't support non-interactive configuration. For the `discover` skill, we need to configure veripak programmatically. The config file at `~/.config/veripak/config.json` works, but a `veripak config set <key> <value>` command (like sanicode has) would be cleaner.
- The `_agent.attempts` and `_agent.errors` fields in the output are useful for debugging but should probably be behind a `--verbose` flag rather than always included.

**Spec integration notes:**
- The `discover` skill should parse dependency manifests (pom.xml, requirements.txt, pyproject.toml) to extract package names and versions, then run veripak on each.
- Use veripak's `summary.urgency` field directly as the spec's `urgency` enum value.
- Cross-validate CVE IDs from veripak against the raw OSV/NVD sources before marking them as `confidence: high` in the spec.
