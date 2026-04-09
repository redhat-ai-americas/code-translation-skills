# Retrospective: M0 Spec Schema

**Date:** 2026-04-09
**Effort:** Define the spec JSON schema, produce worked examples for Java and Python, build the Markdown review pipeline.
**Commits:** `5238c5b`

## What We Set Out To Do

Define the M0 spec schema deliverable: a JSON schema for the specification format, at least two worked examples (Java + Python), and a derived Markdown view template for human review. The schema needed to support the full hierarchy (system→module→function), cross-cutting facets, and metadata on every element.

The NEXT_SESSION.md prompt also asked us to ground the design in reality by manually extracting what the spec should say about real functions from real open-source projects.

## What Changed

| Change | Type | Rationale |
|--------|------|-----------|
| Ran all four foundation tools (treeloom, greploom, sanicode, veripak) before designing the schema | Good pivot | User challenged a theoretical claim about facet attachment; empirical testing disproved the separate-documents approach |
| Inline facets instead of separate cross-cutting documents | Good pivot | Treeloom data is already node-centric; separate documents would fragment naturally cohesive information |
| Configured all tools with Granite 3.3 8b via local Ollama | Added scope | Proved the local-LLM workflow works for all tools; found performance issues with sanicode on larger scans |
| Added `class` as a hierarchy level | Good pivot | Java code makes class-level meaningfully different from module-level |
| Added `test_evidence` source and `disputed` status to metadata enums | Good pivot | Tests are partial behavioral specs; human reviewers may disagree with LLM extractions |
| Spec layers on CPG (required companion artifact) rather than being self-contained | Good pivot | Avoids re-encoding structural data; CPG is always reproducible from source |

## What Went Well

- **Empirical-first design.** Running the tools first, then designing the schema, produced a schema that directly receives tool output with minimal transformation. No speculative abstractions.
- **Clean tool→spec mapping.** Each tool populates a distinct part of the spec with no overlap: treeloom→hierarchy, sanicode→security_findings, veripak→ecosystem_dependencies, greploom→agent retrieval (not stored in spec).
- **Validation on first try.** Both worked examples passed schema validation without edits. The schema was tight enough to catch real errors but not so strict it rejected valid data.
- **Parallel execution.** Running four tool agents concurrently cut wall-clock time significantly. The tools are genuinely independent.
- **The framing-anchor pattern did not recur.** The user challenged an assumption ("Is that true? Clone a repo and see"), and the response was to test empirically rather than defend the theory. This is the countermeasure from previous retros working.

## Gaps Identified

| Gap | Severity | Resolution |
|-----|----------|------------|
| Sanicode only supports Python — Java codebases have no security findings | Known limitation | #31 filed for Java support |
| Veripak CVE agent hallucinated CVE-2015-3117 for jsoup (actually an Adobe Flash CVE) | Quality concern | Documented in tool-feedback.md; Granite 3.3 8b too small for reliable CVE attribution |
| Veripak Maven coordinate query returned stale version (1.15.4 vs 1.21.1) | Bug | Documented in tool-feedback.md |
| Sanicode timed out on full dateutil scan (17 files); LLM calls per-finding are slow | Performance | Scoped to parser/ subdirectory; documented in tool-feedback.md |
| No automated test that render.py works | Follow-up | Manual verification done; pytest would prevent regressions |
| CPG node IDs embed absolute paths (not portable across machines) | Accept for now | Spec is generated per-machine; noted in tool-feedback.md for treeloom improvement |
| SC050 findings (CWE-913) had empty compliance/remediation fields | Sanicode bug | Documented in tool-feedback.md |
| No `code-translation-kit init` CLI entry point yet | Follow-up | #32 filed |

## Action Items

- [x] File sanicode Java support issue (#31)
- [x] File `init` command issue (#32)
- [x] Write tool feedback document for package maintainer (`planning/code-translation-kit/tool-feedback.md`)
- [ ] Verify sanicode Java support works against jsoup after implementation (#31)
- [ ] Add pytest for render.py validating both examples

## Patterns

**Continue:** Testing assumptions against real data before committing to a design. The "clone a repo, run the tools, see what happens" approach produced a better schema than the theoretical proposal would have.

**Continue:** Parallel sub-agents for independent tool runs. Four tools running concurrently is the right workflow.

**Start:** When the `discover` skill is built, have it check for existing artifacts (CPG, greploom index) before re-running tools. The user specifically called this out: "if the CPG is already there, the LLM would not have to run them."

**Start:** Cross-validate LLM-generated CVE attributions against raw OSV/NVD data before marking as high-confidence. Granite 3.3 8b hallucinated at least one CVE ID.
