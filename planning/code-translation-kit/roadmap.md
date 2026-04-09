# Roadmap

Updated 2026-04-09 after the vertical-plane-spec design session. Supersedes the earlier 8-milestone build plan (see git history for the previous version).

## The vertical plane model

The kit is organized around a central artifact: **the specification**.

```
Old Code  -->  [ Extraction ]  -->  SPECIFICATION  -->  [ Generation ]  -->  New Code
                 (left side)        (the plane)          (right side)
```

The spec is a language-neutral, machine-readable, human-reviewable description of what an application does. It's structured hierarchically (system -> subsystem -> module -> function) with cross-cutting facets (data model, usage paths, taint/trust, ecosystem dependencies).

The left side extracts understanding from existing code and produces the spec. The right side generates new code from the spec in any target language. The spec severs the source language's influence on the target implementation -- the right-side agent never sees source code, only the spec.

This makes the N*M problem (every source language to every target language) into N+M: N extractors and M generators, with the spec as lingua franca.

**Key decisions (2026-04-09):**

- Always produce the spec, even for same-language upgrades (Java 8->17). If it proves too heavyweight for small projects, we can make it optional later.
- Human-in-the-loop is a first-class design concern. The agent maximizes the value of each human interaction, not minimizes human involvement.
- Mode A (transform) and Mode B (spec-driven rewrite) from the earlier design collapse into one flow. The spec is always produced. Mechanical tools are accelerators within generation, not a separate path.

## The spec as the central artifact

Every spec element carries metadata:

- **confidence:** `high` | `medium` | `low`
- **source:** `static_analysis` | `llm_inference` | `human_input`
- **status:** `extracted` | `needs_review` | `confirmed`
- **assigned_to:** `agent` | `human` | `domain_expert`

The spec hierarchy:

```
System spec           <-- what the whole thing does, in business terms
  |
Subsystem specs       <-- bounded contexts, data ownership, inter-system contracts
  |
Module specs          <-- public API, invariants, data shape, state ownership
  |
Function contracts    <-- behavioral contracts (observable behavior)
  |
Code graph            <-- treeloom output (structural foundation)
```

Cross-cutting facets at every level:

- **Data model** -- entities, relationships, cardinality, invariants, lifecycle
- **Usage paths** -- call chains, request flows, event propagation
- **Taint/trust** -- sensitive data entry, flow, sanitization, trust boundaries
- **Ecosystem dependencies** -- "needs capability Y, currently provided by library X"

## Human-in-the-loop design

Three interaction points, each designed to maximize the value of the human's time:

1. **During extraction (left side).** The agent flags low-confidence extractions. *"I think this function computes shipping cost with tax, but the logic branches on a magic constant `0.0825` -- please confirm."* The human resolves ambiguity that the code doesn't self-document.

2. **At the spec (the plane).** The agent delivers a spec with gaps explicitly marked. The human team rounds out the spec -- probably with AI assistance, but with human judgment driving. This is where architectural decisions and domain knowledge get captured.

3. **During generation (right side).** The agent pauses at decision points the spec flagged. *"The spec says 'needs caching' but doesn't specify eviction policy -- the source used LRU with 5-minute TTL, keep that or revisit?"* The human makes design decisions the spec intentionally left open.

**Principle:** Don't ask things the code already answers. Don't guess at things only humans know. Route the right questions to the right moment.

## Milestones

### Milestone 0 -- Foundation: Repo Setup, Spec Schema, Project Tracking

**Names:**

- **Repo:** `code-translation-skills` (existing, under `redhat-ai-americas`)
- **PyPI package / kit name:** `code-translation-kit`
- **Claude plugin:** name TBD when we get there

**Repo restructure:**

- Reorganize existing repo to match the kit's directory layout
- Standard scaffolding already in place (LICENSE, CONTRIBUTING, .gitignore, .gitleaks.toml)
- Target layout:

```
code-translation-skills/
  skills/                # SKILL.md files
  profiles/              # YAML profiles per source->target pair
  adapters/              # thin wrappers around external tools
  spec-schema/           # JSON schema for the specification format
  references/            # migration knowledge
  templates/             # project tracking templates (GitHub, GitLab)
  docs/
  examples/              # small reference codebases for testing
  planning/              # design docs (this directory)
```

**Spec schema:**

- JSON schema defining the full spec format
- Hierarchy levels: system -> subsystem -> module -> function
- Cross-cutting facets: data model, usage paths, taint/trust, ecosystem dependencies
- Metadata model on every element: confidence, source, status, assigned_to
- Derived Markdown view template for human review

**Project tracking:**

- `manage-project` skill with templates for both GitHub Issues and GitLab Issues
- Issue taxonomy: milestones as epics, spec sections as trackable items
- Board setup with standard columns
- Decision tracking for regulated-environment auditability
- Early decision: all migration work tracked in issues from day one

**Reference codebases:**

- At least one small open-source project per language for testing (Java, Python minimum)

**Done when:** spec schema is defined, repo is set up with tracking, a human can look at an empty spec and understand what needs filling in at every level.

### Milestone 1 -- Left Side: Machine Extraction

Populate the spec from real code using deterministic tools.

**Skills:**

- `discover` -- orchestrate treeloom, veripak, sanicode/semgrep to build foundation artifacts
- `library-replacement` -- import mapping via YAML mapping files *(already built)*

**What gets populated:**

- Code graph -> spec structure (modules, functions, types, call relationships)
- Data model -> types, schemas, relationships
- API surface -> function signatures, endpoints, message contracts
- Dependency graph -> ecosystem dependency facet
- Security/taint -> trust boundary facet
- Control flow, data flow -> usage path facet

**Testing discipline:** Identify existing test coverage. Tests are partial behavioral specs that feed into M2.

**Done when:** extraction against reference codebases produces a spec ~40-50% populated with high-confidence, machine-extracted elements. Tested on at least two languages to prove language-agnosticism early.

### Milestone 2 -- Left Side: LLM Extraction

Layer LLM reasoning on top of the machine foundation to populate the portions of the spec that require understanding intent.

**Skills:**

- `extract-contracts` -- behavioral contracts at function level
- `extract-intent` -- business rules, domain logic, state lifecycle, the "why" behind structures

**What gets populated:**

- Behavioral contracts (what each function does, observable behavior)
- Business rules and invariants
- Error handling semantics (not just "throws X" but "what should happen when Y fails")
- State lifecycle (what state exists, how it transitions, what persists)
- Intent annotations

Every LLM-extracted element gets `confidence: medium`, `source: llm_inference`, `status: needs_review`.

**Testing discipline:** Validate extracted contracts against existing tests. If tests say `f(2, 3) == 5` and the extracted contract says "f computes the product," flag the discrepancy.

**Done when:** spec goes from ~50% to ~75% populated. Remaining ~25% explicitly flagged for human input.

### Milestone 3 -- The Plane: Spec Review & Completion

Build the workflow for humans to review and complete the spec. This milestone is about the **process**, not just artifacts.

**Skills:**

- `review-spec` -- filtering, completeness assessment, human input capture
- `dashboard` -- visual status of spec completion and migration progress

**Workflow:**

- Filter by: needs_review, low confidence, assigned to domain expert, by facet, by hierarchy level
- Human input capture with attribution and timestamps (audit trail for regulated environments)
- Completeness rubric: "is this spec ready for generation?"
- Reviewer's guide: what you're looking at, what decisions you need to make, how to flag disagreements

**Project tracking integration:** Spec review items tracked as issues. Decisions captured with context.

**Done when:** a developer can sit down with an extracted spec, understand what's been done, see what needs their input, make decisions, and produce a spec marked "ready for generation."

### Milestone 4 -- Right Side: Generation

Produce target code from the spec. The right-side agent never sees source code.

**Skills:**

- `map-architecture` -- spec concepts -> target language idioms and patterns
- `scaffold-target` -- project structure, build system, dependency management for target
- `generate-from-spec` -- module-by-module, function-by-function generation
- `convert-mechanical` -- mechanical tool acceleration where available (OpenRewrite for Java, libcst for Python) as an optimization, not a replacement for spec-driven generation

**Human interaction:** Agent pauses at decision points the spec flagged as ambiguous.

**Testing discipline -- spec-driven TDD:**

1. Generate test cases FROM spec contracts before generating implementation
2. Generate implementation that passes those tests
3. Tests are genuinely independent of implementation because they derive from the spec, not the code

**Done when:** a spec produced from a reference codebase (language A) generates a working project in language B, with at least one module fully implemented and tests passing.

### Milestone 5 -- Verification

Close the loop. Does the generated code satisfy the spec?

**Skills:**

- `verify-translation` -- contract verification, confidence scoring
- `report-gaps` -- what's missing, what failed, what needs human attention

**Verification layers:**

| Layer | What it validates |
|---|---|
| Unit tests (generated in M4) | Individual function contracts |
| Integration tests | Module composition, data flow between components |
| Smoke tests | Critical paths work end-to-end |
| Gap analysis | What verification couldn't cover |

**Iterative loop:** Verification failures feed back to the agent for correction. The agent re-generates, re-verifies, or escalates to human.

**Done when:** verification produces quantitative confidence scores (per-function, per-module, overall) and a human-readable report of what passed, failed, and needs attention.

### Milestone 6 -- Architecture Assessment (the killer feature)

Propose alternative module decompositions. This changes the **spec**, not the code.

**Skills:**

- `propose-decomposition` -- graph clustering + LLM scoring

**Flow:**

1. Graph clustering on treeloom output (Louvain/Leiden + hierarchical agglomerative)
2. LLM scoring of candidates (cohesion, coupling, size balance, domain-naming heuristics)
3. Present alternatives to humans with trade-offs and visualizations
4. Human selects a decomposition
5. Spec rewritten to reflect new module boundaries
6. M4-M5 run against the restructured spec

**This milestone deserves a dedicated research session** before implementation to settle clustering algorithm selection, scoring rubric design, and presentation format.

**Done when:** given a codebase with poor module boundaries, the tool proposes at least two alternatives a human architect agrees are improvements, and one can be carried through generation and verification.

### Milestone 7 -- Polish & Real-World Validation

- Full pipeline on a non-trivial open-source project end-to-end
- UAT -- humans verify generated system against system-level spec
- Documentation completion (docs-reorg pass, then docs-refresh as ongoing health check)
- Dashboard rebuild
- First external user feedback

## Cross-cutting disciplines

These are not milestones. They thread through every milestone.

### Human-in-the-loop

Described in detail above, but worth calling out as a discipline, not just a principle:

- **M1:** Agent flags low-confidence machine extractions for human review
- **M2:** LLM-extracted elements default to `status: needs_review`; discrepancies between contracts and existing tests flagged
- **M3:** The entire milestone is the human review workflow
- **M4:** Agent pauses at decision points the spec flagged as ambiguous
- **M5:** Verification failures that the agent can't self-correct escalate to human
- **M6:** Human selects which decomposition alternative to pursue

Every milestone should be designed so the agent knows *when* to ask and *what* to ask, rather than guessing or blocking.

### Project tracking & auditability

- **M0:** Set up tracking infrastructure (GitHub or GitLab, via `manage-project` skill)
- **Every milestone:** Produces traceable deliverables
- **The spec's metadata** (source, status, assigned_to, timestamps) provides an audit trail without extra paperwork
- **Regulated environments:** Decision capture, human attribution on spec elements, confidence scoring -- all designed to survive audit

### Documentation

Documentation accretes per milestone, not piled up at the end:

- **M0:** Architecture decision records, spec schema reference
- **M1-M2:** How extraction works, known limitations
- **M3:** Reviewer's guide -- the most important doc for adoption
- **M4-M5:** How generation and verification work, interpreting confidence scores
- **M7:** docs-reorg pass to clean up, docs-refresh as ongoing hygiene

### Testing

Tests play different roles on each side of the vertical plane.

**Left side -- old tests as spec inputs:**

- Existing tests are partial behavioral contracts
- They validate extracted specs: does the contract match what the tests verify?
- Coverage gaps are information the spec should carry
- Old tests inform extraction; they do not gate progress

**Right side -- spec-driven TDD:**

- Generate tests from spec contracts before generating implementation
- Tests are independent of implementation (derived from spec, not code)
- Verification layers stack: unit -> integration -> smoke -> UAT

**Old tests do not need to pass first.** They're evidence for extraction, not a prerequisite. Some old tests are tied to source-language idioms that don't translate -- those are implementation tests, not behavior tests, and shouldn't block anything.

## Skills inventory

**Left side (extraction):**

1. `discover` -- foundation artifacts: treeloom graph, veripak audit, security baseline
2. `library-replacement` -- import mapping via YAML mapping files *(already built)*
3. `extract-contracts` -- behavioral contracts (function -> module -> system)
4. `extract-intent` -- business rules, domain logic, state lifecycle

**The plane (spec management):**

5. `review-spec` -- human review workflow, completeness assessment
6. `propose-decomposition` -- alternative module boundaries via graph clustering *(M6)*
7. `dashboard` -- visual status of spec completion and migration progress

**Right side (generation):**

8. `map-architecture` -- spec concepts -> target language idioms
9. `scaffold-target` -- project structure in target language
10. `generate-from-spec` -- module-by-module code generation
11. `convert-mechanical` -- mechanical tool acceleration (OpenRewrite, libcst, etc.)

**Verification:**

12. `verify-translation` -- contract verification, confidence scoring
13. `report-gaps` -- what's missing, what failed, what needs human attention

**Project management:**

14. `manage-project` -- GitHub/GitLab templates, issue taxonomy, board setup, decision tracking

**Context retrieval:**

15. `retrieve-context` -- greploom wrapper for agent codebase exploration

Subject to refinement. The old suite had 34 skills; this one has 15, each doing more.

## Foundation tools

The kit delegates to purpose-built packages rather than reimplementing:

| Concern | Tool | Languages |
|---|---|---|
| Code graph (AST + CFG + DFG + call graph) | **treeloom** | Python, JS/TS, Go, Java, C, C++, Rust |
| Context retrieval | **greploom** | Whatever treeloom supports |
| Dependency audit | **veripak** | PyPI, npm, Maven, Go, NuGet, etc. |
| SAST with compliance mapping | **sanicode** | Python, JS/TS, PHP |
| SARIF -> STIG/NIST compliance | **stigcode** | Any SARIF input |
| Java mechanical conversion | **OpenRewrite** | Java (see `openrewrite-findings.md`) |
| Python mechanical conversion | **libcst** | Python |

Gaps: Java SAST (use Semgrep until sanicode adds Java), JS/TS mechanical (jscodeshift or ts-morph -- choose when needed).

## Profiles

Profiles are declarative YAML config, not code. A profile declares engine choices and tool configurations for a source->target pair (mechanical engine, SAST tool, build/test commands, dependency manifests). See git history for the detailed profile YAML examples from the earlier architecture doc.

Adding a new language pair = new profile + adapter (if the mechanical engine is new). Skills themselves are language-agnostic.

## What makes a milestone done

1. An agent can complete it on a real (small) open-source codebase without hand-holding
2. The spec artifacts produced are valid against the schema
3. A human reviewer can understand the artifacts without reading the source code
4. The milestone's deliverables are documented and tracked in issues
5. If the agent gets stuck or drifts, the fix is to sharpen the skill -- not add orchestration

## Explicit non-goals

- Phase runner scripts
- Gate checkers that block agent progression
- Hand-rolled graph building, security scanning, dependency auditing
- Pattern catalogs for things external tools already handle
- Rigid pipeline sequencing -- the agent decides order within a milestone
- 100% automation -- the human-in-the-loop is a feature, not a limitation

## Sequencing notes

- **M0-M1** are the critical path. They test whether the spec-centric approach and tool delegation work in practice.
- **M3** (spec review workflow) is the adoption gatekeeper. If humans can't review and complete specs, nothing downstream matters.
- **M4-M5** (generation + verification) can iterate rapidly once the spec is solid.
- **M6** (propose-decomposition) is the demo-generating killer feature. Deserves a dedicated research session before implementation.
- **M4 and M6** can be parallelized if multiple people work on the kit.
- Nothing is urgent. No live engagement driving dates. Sequencing is about learning and validation, not delivery pressure.

## Open questions

Carried forward from the previous planning docs. Organized by when they need resolution.

**Blocking M0 (spec schema):**

- **Spec format details.** JSON as source of truth + Markdown as derived view. Needs a concrete schema. C4 model might inform subsystem/system levels but doesn't map directly to module-level specs.
- **Architecture doc format.** Leaning Mermaid in Markdown. Confirm once we see what the graph output actually looks like.

**Blocking M1 (machine extraction):**

- **Dependency manifest detection.** How does the profile declare where dependency files live? Glob patterns in profile.yaml are probably enough. Needs concrete schema.
- **Test runner abstraction.** Probably "shell command string in profile." But how does the agent distinguish a meaningful test failure from a runner startup error or missing dependency?
- **Treeloom invocation format.** CLI with JSON output (agent-friendly) vs Python library import (Python-specific). Probably CLI.

**Blocking M4 (generation):**

- **Scaffolder opinionation.** How opinionated should `scaffold-target` be about target project structure? Ship reasonable defaults per language with overrides in the profile.
- **Generation granularity.** Whole modules in one shot, or function-by-function? Probably function-by-function within a module, with the module spec as binding contract.

**Blocking M6 (propose-decomposition):**

- **Clustering algorithm selection.** Louvain/Leiden + hierarchical agglomerative as starting pair. Deserves a dedicated research session.
- **Scoring rubric.** What does "better decomposition" mean mechanically? Cohesion, coupling, size balance, domain-naming, stability.
- **Presentation format.** Dashboard with side-by-side module diagrams + text report. Needs design.

**Parked (future):**

- Dashboard extensions for spec-driven generation artifacts (decide after M4 produces real output)
- MCP deployment guide (post-v1, when a team asks for it)
- Profile versioning scheme (once schema is stable)
- Incremental re-analysis (treeloom supports incremental rebuild; skill layer would need to also)
- Cross-profile composition (can you chain Python 2->3 + Python 3->modern as two profiles?)

**OpenRewrite items to verify:**

- Whether general `ClassToRecord` recipe has landed in `rewrite-migrate-java`
- Whether JPMS `module-info.java` generator recipe exists
- Per-recipe license (Apache vs Moderne Source Available) on specific recipes the kit would use
- Moderne CLI licensing terms for automated/agent use
