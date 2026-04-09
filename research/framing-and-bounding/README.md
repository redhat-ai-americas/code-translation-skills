# Framing and Bounding — why AI agents need them, and why this project is about them

**Status:** Stub. Captured from a 2026-04-08 retrospective observation. Expand into a proper research/exposition document when there's appetite.

## The thesis in one paragraph

Any LLM behind an agent will over-index on what is already in its context. When the task involves an old or legacy artifact, the model's next-token probabilities activate pathways for dealing with that artifact *in the familiar way* — even when the whole point of the work is to do something new with it. The remedy is not a bigger model; it is deliberate framing and bounding at the start of the work: clear goal-in-target-terms framing, memories that shape the prior, explicit rules that rule out familiar-but-wrong paths, and skills that reinforce the intended workflow. Proper framing converts *"I see an old thing, therefore the natural next step is [the old thing's usual handling]"* into *"Of course I see an old thing — dealing with old things is exactly what we're here for, so let's plan how to do [the new thing]."*

## Why this belongs in the `code-translation-skills` pitch

This is not a side observation. It is the reason the project exists at all.

A naive agent pointed at a Python 2 codebase will start offering Python 2 fixes. A naive agent pointed at a COBOL program will start explaining COBOL. A naive agent pointed at a legacy Java service will start modernizing within Java. None of those are translation. They are all the old artifact pulling the agent into old-artifact behavior.

The skills in this repo exist so that the starting artifact does not define the task. The *target* defines the task. The skills — plus their bundled framing, rules, and memories — keep the agent bounded to the translation goal instead of letting the source language's gravitational pull take over.

## Evidence from sessions

### 2026-04-08 bootstrap session — the naming incident

During the repo handoff to `redhat-ai-americas`, the assistant proposed renaming the repo to `code-modernization-skills`. The user pushed back with a simple stress test: *what if a customer wrote a brand-new Java app yesterday and now wants to translate it to Rust?* Both sides are modern. "Modernization" does not fit. The proposed name collapsed.

The failure was not in naming reasoning. It was that the assistant had silently let the py2to3 artifacts in the repo become a frame for the *whole project*, narrowing its sense of scope to "legacy → modern" when the real scope is "any source → any target." This happened with no bad intent — the model was doing what models do. The lesson is that *good intent and good reasoning are not enough*; the framing has to be made explicit up-front, or the visible artifacts will quietly take over.

See `retrospectives/2026-04-08_code-translation-skills-bootstrap/RETRO.md` for the full write-up.

## Open threads to develop

Things the research document, when written, should cover:

- **Mechanism.** What is actually happening at the token-probability level when "I see X" drifts into "therefore do [familiar thing with X]"? How much of this is attention over the context window, how much is prior, and how much is instruction-tuning defaults?
- **Countermeasures.** A taxonomy of framing/bounding techniques and when each is appropriate: system prompts, skill cards, memories, explicit rules, agent personas, structured outputs, refusal patterns, etc.
- **Concrete examples.** A gallery of sessions where framing saved the translation, and sessions where the lack of it caused drift. The 2026-04-08 naming incident is one data point; more would make the argument.
- **Measurement.** How do we know framing is working? Can we construct a benchmark where a well-framed agent and a naively-framed agent both receive the same legacy artifact, and we measure how often each one drifts into source-side behavior vs. stays bounded to the target?
- **Connection to the skill architecture.** How do the existing skills in this repo encode framing today (implicitly or explicitly), and where could they be strengthened?
- **Pitch positioning.** How to explain this to a skeptical stakeholder in three sentences without leaning on AI jargon.

## Related

- `retrospectives/2026-04-08_code-translation-skills-bootstrap/RETRO.md` — source of this stub
- `planning/agent-kit-generalization/` — related brainstorming on generalizing the skill suite beyond py2to3; framing and bounding are a critical part of that generalization
