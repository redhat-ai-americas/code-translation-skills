# Code Translation Kit — Planning

Planning notes for `code-translation-kit`, a language-agnostic agent kit that helps migrate codebases between language versions or entirely different languages. Designed for coding agents (Claude Code, OpenCode) and agent-loop-native from day one.

- **Repo:** `code-translation-skills` (under `redhat-ai-americas`)
- **PyPI package name:** `code-translation-kit`

## Current state (2026-04-09)

The project pivoted from a Python 2->3 focused skill suite (34 fine-grained skills with phase runners and gate checkers) to a **vertical plane model**: old code on the left, new code on the right, a complete specification as the dividing plane between them. The spec is always produced -- even for same-language upgrades. Human-in-the-loop is a first-class design concern, not an afterthought.

## Core design principles

1. **The vertical plane.** The specification is the central artifact. The left side extracts it from source code. The right side generates target code from it. The spec severs the source language's gravitational pull on the target.

2. **Always produce the spec.** Even for same-language upgrades (Java 8->17). The spec catches intent mismatches mechanical tools miss. If it becomes too heavyweight for small projects, consider making it optional later.

3. **Human-in-the-loop by design.** The agent maximizes the value of each human interaction. Flags low-confidence extractions. Delivers specs with explicit gaps. Pauses at decision points. The human-in-the-loop is a feature, not a limitation.

4. **Agent-loop-native.** Skills describe intent and verification. The agent handles sequencing. No phase runners. No gate checkers. If the agent drifts, sharpen the skill.

5. **Delegate to purpose-built tools.** treeloom, greploom, veripak, sanicode, stigcode, OpenRewrite, libcst. Don't reimplement what exists.

6. **The killer feature is proposing alternative module decompositions.** Graph clustering + LLM scoring proposes better boundaries than the source has. Humans pick. This changes the spec before generation.

7. **Profiles are data, not code.** Adding a new language pair = new YAML profile + adapter. Skills are language-agnostic.

8. **Project tracking from day one.** Templates for GitHub and GitLab. Decision capture for regulated environments. The spec's metadata provides an audit trail.

## Foundation tools

| Concern | Tool | Languages |
|---|---|---|
| Code graph | **treeloom** | Python, JS/TS, Go, Java, C, C++, Rust |
| Context retrieval | **greploom** | Whatever treeloom supports |
| Dependency audit | **veripak** | All major ecosystems |
| SAST | **sanicode** | Python, JS/TS, PHP |
| Compliance artifacts | **stigcode** | Any SARIF input |
| Java mechanical | **OpenRewrite** | Java |
| Python mechanical | **libcst** | Python |

## Files in this directory

- `README.md` -- this file
- `roadmap.md` -- the vertical-plane-model milestone plan (M0-M7), skills inventory, open questions
- `research.md` -- the five PyPI packages: what each does, how each fits
- `openrewrite-findings.md` -- Java AST transformation engine research

Earlier design documents (architecture notes, open questions, session transcripts) are preserved in git history.

## Decisions recorded

| Decision | Resolution | Date |
|---|---|---|
| Repo name | Stay with `code-translation-skills` | 2026-04-09 |
| Package name | `code-translation-kit` (available on PyPI) | 2026-04-09 |
| Central artifact | The specification -- always produced | 2026-04-09 |
| Mode A vs Mode B | Collapsed into one flow; spec always produced | 2026-04-09 |
| Human-in-the-loop | First-class design concern with three interaction points | 2026-04-09 |
| Project tracking | GitHub/GitLab templates, tracked from day one, audit-ready | 2026-04-09 |
| Orchestration approach | Agent-loop-native; no phase runners, no gate-blocking | 2026-04-08 |
| Java mechanical engine | OpenRewrite | 2026-04-08 |
| Python mechanical engine | libcst | 2026-04-08 |
| Killer feature | `propose-decomposition` -- graph clustering + LLM scoring | 2026-04-08 |
| Deployment | CLI default, MCP optional | 2026-04-08 |

## Next steps

- **Define the spec schema** (M0) -- the first concrete deliverable
- **Build the `manage-project` skill** with GitHub/GitLab templates
- **Prototype M1** (machine extraction) on a small Java + Python codebase
- **Dedicated research session** on `propose-decomposition` (M6) when ready

See `roadmap.md` for the full milestone plan and open questions.
