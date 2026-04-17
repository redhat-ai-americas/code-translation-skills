# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

A toolkit for code translation/migration organized around the **vertical plane model**: a language-neutral specification sits between extraction (old code) and generation (new code). The spec is always produced, even for same-language upgrades (e.g. Java 8 to 17), to sever the source language's gravitational pull on the target.

```
Old Code  -->  [ Extraction ]  -->  SPECIFICATION  -->  [ Generation ]  -->  New Code
                 (left side)        (the plane)          (right side)
```

The spec (`spec.json`) is the central artifact. Everything feeds into it or reads from it.

## Architecture

### Skills (`skills/`)

Each skill is a self-contained directory with a `SKILL.md` (agent instructions) and implementation scripts. Skills are designed to be invoked by Claude Code agents, not run as standalone CLI tools (though the scripts can be run directly).

| Skill | Milestone | What it does |
|---|---|---|
| `discover` | M1 | Orchestrates treeloom/greploom/sanicode/veripak to produce a skeleton `spec.json` with structure and security data, contracts left empty |
| `extract-contracts` | M2 | Queries greploom for source context, prompts an LLM to infer behavioral contracts, writes them into the spec |
| `library-replacement` | M2 | Identifies imports needing replacement via treeloom, applies YAML mapping files |

### Spec schema (`spec-schema/`)

- `spec.schema.json` — JSON Schema (Draft 2020-12) defining the spec format
- `examples/` — Hand-crafted gold-standard specs for dateutil-parser and jsoup-safety (used for comparison/evaluation)
- `render.py` — Validates spec against schema and renders to Markdown via Jinja2
- `templates/spec-review.md.j2` — Review template

### Spec structure

Top-level sections: `meta`, `cpg_ref`, `elements`, `security_findings`, `ecosystem_dependencies`, `usage_paths`.

Elements are keyed by human-readable IDs using prefixes: `mod:`, `cls:`, `fn:`. Each element carries a `contract` (purpose, preconditions, postconditions, invariants, side_effects, error_conditions, trust_boundary) and `metadata` (confidence, source, status).

### External tool dependencies

The kit delegates to purpose-built tools rather than reimplementing analysis:

| Tool | Purpose | Install |
|---|---|---|
| **treeloom** (0.9.0+) | Code property graph builder (AST + call graph) | `pip install treeloom` |
| **greploom** (0.5.0+) | Semantic search over CPGs | `pip install greploom` |
| **veripak** | Dependency audit (CVEs, licenses) | `pip install veripak` |
| **sanicode** | SAST with compliance mapping | `pip install sanicode` |

### Reference codebases (external)

These live outside this repo at `~/Developer/`:

- `dateutil-example/` — Python. 17 source files, 372 elements. Primary test subject for extraction.
- `jsoup-example/` — Java. 184 source files, 4547 elements. Secondary test subject.

Each contains: `cpg.json`, `greploom.db`, `spec.json`, sanicode/veripak outputs.

## Running the scripts

All scripts are standalone Python, no package install required. The venv at `.venv/` has dependencies (requests, jsonschema, jinja2).

```bash
# Rebuild a skeleton spec from CPG + tool outputs
python3 skills/discover/assemble.py \
  --cpg ~/Developer/dateutil-example/cpg.json \
  --project-name dateutil-parser --language python --source-root dateutil \
  --sanicode ~/Developer/dateutil-example/sanicode-result.json \
  --veripak ~/Developer/dateutil-example/veripak-python-dateutil.json \
  --cpg-rel-path cpg.json -o ~/Developer/dateutil-example/spec.json

# Extract contracts (with resume support)
python3 skills/extract-contracts/extract.py \
  --spec ~/Developer/dateutil-example/spec.json \
  --greploom-db ~/Developer/dateutil-example/greploom.db \
  --cpg ~/Developer/dateutil-example/cpg.json \
  --llm-endpoint https://gpt-oss-20b-gpt-oss-model.apps.cluster-n7pd5.n7pd5.sandbox5167.opentlc.com \
  --scope "mod:parser" --skip-existing

# Compare extracted contracts against gold standard
python3 skills/extract-contracts/compare.py \
  --extracted ~/Developer/dateutil-example/spec.json \
  --reference spec-schema/examples/dateutil-parser.spec.json \
  --id-map "mod:parser=mod:dateutil.parser"

# Validate and render spec to Markdown
python3 spec-schema/render.py \
  --spec ~/Developer/dateutil-example/spec.json \
  --schema spec-schema/spec.schema.json \
  --template spec-schema/templates/spec-review.md.j2
```

## Rebuilding CPGs and indexes

When treeloom or greploom versions change, or source code changes:

```bash
# Build CPG (scope to source root, include source text)
cd ~/Developer/dateutil-example
treeloom build --include-source --language python -o cpg.json src/

# Rebuild greploom index (must specify --db explicitly)
greploom index --force --db greploom.db cpg.json
```

After rebuilding CPGs, the skeleton spec must be regenerated (node IDs change with line numbers). Existing contracts are lost — back up `spec.json` first.

## Key conventions

- **Source text lives in `attrs.source_text`** in CPG nodes, not a top-level field. Greploom exposes it in the `text` field of query results when `--include-source` is passed.
- **Element IDs** use the pattern `{prefix}:{qualified.name}` where prefix is `mod:`, `cls:`, or `fn:`. The qualified name is derived from the file path relative to the source root.
- **`--scope` filtering** in extract.py uses prefix matching on element IDs. E.g. `--scope "mod:parser"` captures the parser module and all its children.
- **Model choice**: gpt-oss-20B for quality, granite-8B as fallback for elements that timeout. vLLM endpoints drop ~15% of large prompts; `--skip-existing` handles this.

## Known issues

- vLLM connection drops on large prompts (~15% failure rate). Mitigated by `--skip-existing` resume. See issue #34.
- Module-level contracts are weak (modules have minimal source in greploom).
- LLM tends to use "fatal" severity where gold standard says "recoverable".
- No test suite yet (issue #33).

## Planning and history

- `planning/code-translation-kit/roadmap.md` — Full roadmap (M0-M7), vertical plane model design
- `retrospectives/` — Session retrospectives with recurring patterns and action items
- `NEXT_SESSION.md` — Handoff notes for the next session (gitignored, local only)
