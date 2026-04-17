# Retrospective: M1 Discover Skill

**Date:** 2026-04-17
**Effort:** Build the `discover` skill — M1 entry point that produces skeleton spec.json from foundation tools
**Commits:** 5003d25
**Issues filed:** rdwj/treeloom#98, rdwj/treeloom#99, rdwj/sanicode#242, rdwj/veripak#27

## What We Set Out To Do

From NEXT_SESSION.md, five acceptance criteria:

1. `skills/discover/SKILL.md` — complete skill definition
2. Working runs against both jsoup (Java, 91 files) and dateutil (Python, 17 files)
3. Produced specs validate against `spec-schema/spec.schema.json`
4. Produced specs render to readable Markdown via `render.py`
5. Stub elements for every module, class, and function with metadata `extracted/static_analysis/high` and empty contracts

## What Changed

| Change | Type | Rationale |
|--------|------|-----------|
| Dropped profile format (YAML config) — CLI args to assemble.py instead | Good pivot | Profiles are M3+; adding them now would be speculative complexity for zero benefit |
| Used `scope` field for parent linkage instead of `contains` edges | Good pivot | Discovered during implementation that raw CPG has a `scope` field. Simpler and more accurate than walking 7588 contains edges |
| Full rewrite of assemble.py data access after first run failed | Missed requirement | Explored `treeloom query --json` (flattened) during planning but assemble.py reads raw CPG JSON (nested `location`/`end_location`/`scope`). See Gaps. |
| Rebuilt CPGs with treeloom 0.9.0 and relative paths | Scope addition | 350x build speedup + portable node_refs were worth the extra 10 minutes |

## What Went Well

- **Plan mode → parallel implementation** worked cleanly. Plan caught design decisions (element ID naming, parent linkage, schema gotchas) before code was written. Two implementation agents (assemble.py + SKILL.md) ran in parallel with no conflicts.
- **Bug-file-fix-retest cycle.** Four bugs filed against three packages, all fixed same-day. Upgraded versions, re-ran the full pipeline, all specs validated. The tool teams' responsiveness made this session notably productive.
- **NEXT_SESSION.md quality.** The handoff doc was comprehensive — tool CLI reference, known workarounds, execution DAG, design questions, acceptance criteria. Minimal ambiguity at session start.
- **Two-codebase validation.** Testing against both dateutil (Python, 372 elements) and jsoup (Java, 2439 elements with 435 overload collisions) caught issues that a single-language test wouldn't: the Java class-name-matches-file-stem deduplication, the `@line` collision suffix for method overloads, and the `src/main/java` vs `src` source root difference.
- **treeloom 0.9.0 build speed.** jsoup CPG went from 8-9 minutes to 1.5 seconds. This removed the CPG build as a workflow bottleneck entirely. The discover skill's end-to-end time for jsoup is now ~30 seconds instead of 10+ minutes.

## Gaps Identified

| Gap | Severity | Resolution |
|-----|----------|------------|
| Explored `treeloom query --json` during planning but assemble.py reads raw CPG JSON — different structure (`file` vs `location.file`, missing `scope`/`end_location`) | Process gap | Fixed during session (full rewrite). See Patterns. |
| No pytest tests for assemble.py | Follow-up | Two-codebase validation is strong evidence, but regressions from schema or CPG format changes won't be caught automatically |
| greploom indexes not rebuilt with 0.9.0 CPGs | Follow-up | Existing indexes are from the 0.7.0 CPG. Should be rebuilt before M2 uses them for context retrieval |
| Bug-fix turnaround from package teams was same-day — can't count on this | Accept | The workarounds (stdout redirect for sanicode, raw CPG read for treeloom edges) were in place before the fixes landed. Good practice: always have a workaround before filing. |

## Action Items

- [ ] Rebuild greploom indexes against the 0.9.0 CPGs before starting M2
- [ ] Consider adding pytest for assemble.py if the schema or CPG format changes in a future round

## Patterns

**Recurring: Explore the actual data source, not a convenience view of it.** This is a new instance of a familiar pattern — making decisions based on what's most visible rather than what's most accurate. In past retros this manifested as framing-anchor drift (overweighting visible artifacts). Here it manifested as the Explore agent testing `treeloom query --json` output and the implementation agent assuming raw CPG JSON has the same structure. The countermeasure: when planning code that reads a file format, inspect the actual file, not a CLI that transforms it.

**Start:** When an Explore agent is gathering data to inform an implementation, have it inspect the actual input files (e.g., `python3 -c "import json; ..."` on the raw CPG) rather than CLI convenience commands that may transform the data.

**Continue:** Plan mode before non-trivial implementation. This session's plan caught the element ID naming convention, the `additionalProperties: false` gotchas, the collision handling strategy, and the parent linkage approach — all before a line of code was written.

**Continue:** Parallel implementation agents for independent deliverables. SKILL.md and assemble.py had no dependencies and were written simultaneously.

**Continue:** Two-codebase validation across languages. Single-language testing would have missed multiple Java-specific issues.
