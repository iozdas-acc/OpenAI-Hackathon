---
name: maximize-scoring-criteria
description: Optimize hackathon work against an active judging rubric. Use when planning, scoping, implementing, reviewing, or demo-shaping work and the scoring criteria are provided by the user or stored elsewhere in repo context such as AGENTS.md or PLANS.md.
---

# Maximize Scoring Criteria

Use this skill to bias decisions toward the active judging rubric, not just technical completeness.

Pair it with `iteration-stage-gate` when a high-scoring idea risks pulling in later-stage scope.

## Load The Active Criteria

Before using this skill, identify the active rubric from the highest-priority available source:

1. criteria explicitly provided in the user request
2. repo-level agent context such as `AGENTS.md`
3. planning context such as `PLANS.md`

If multiple sources disagree, prefer the most recent user-provided criteria.

Do not hardcode rubric contents into this skill. Treat the rubric as external context that may change between events or teams.

## Required Framing

Before proposing or implementing work:

- identify the real user, partner, or business problem
- state the smallest convincing slice that can be shown in a demo
- identify where Codex materially changes the workflow, not just the code volume
- prefer decisions that improve at least two rubric dimensions at once

## Decision Rules

For each criterion in the active rubric:

- restate what success looks like in practical terms
- identify the strongest evidence the work could show for that criterion
- choose changes that are visible, credible, and easy to explain
- avoid work that is technically impressive but weakly legible to judges

## Common Mappings

Use these heuristic mappings only when they fit the active rubric. They are examples, not fixed categories.

### Codex or AI leverage

- Prefer workflows where Codex helps generate, structure, evaluate, refine, or operationalize the outcome.
- Make Codex part of the product story or delivery story, not a hidden implementation detail.
- Show how repo-managed skills, agent guidance, orchestration, or context awareness improved the result.
- Avoid superficial claims like "Codex helped write code" unless there is a concrete, demo-visible benefit.

### Business or partner impact

Tie the work to a believable external or internal business outcome.

- Name the target user or stakeholder.
- State the pain removed, time saved, quality improved, or risk reduced.
- Prefer workflows that could plausibly be used after the hackathon.
- Avoid novelty without a clear partner outcome.

### Reusability or adoption

Build for repeat use, not a one-off stunt.

- Prefer templates, patterns, shared components, clear docs, and configurable flows.
- Keep setup and handoff simple enough that another team could reuse the output.
- Prefer generalizable workflows over hard-coded edge cases.
- Avoid tightly bespoke implementations unless they unlock a strong demo and can later be generalized.

### Demo or pitch quality

Optimize for a crisp, convincing story.

- Ensure the core flow is visible in a short demo.
- Prefer obvious before-and-after moments.
- Show both the outcome and the workflow.
- Make the value legible to non-engineering judges.
- Avoid hidden infrastructure work unless it directly strengthens the story being shown.

## Working Heuristics

When several options are available, prefer the one that:

1. is demo-visible today
2. proves meaningful Codex leverage
3. solves a concrete partner problem
4. leaves behind reusable assets or patterns

If two options are otherwise equal, choose the simpler one with the clearer demo narrative.

## Demo Guidance

Structure demos and summaries around:

- what was built
- why it matters
- where Codex accelerated or transformed the build

When useful, summarize the work with a four-part score check:

- criterion: what does this rubric dimension require?
- evidence: what will judges actually see?
- tradeoff: what are we deliberately not doing?
- walkthrough: what is the shortest compelling explanation?

## Anti-Patterns

Avoid these unless explicitly requested:

- broad scope with weak proof
- impressive infrastructure that is invisible in the demo
- rubric alignment that is claimed but not evidenced
- polished UI with no credible business value
- bespoke logic that cannot be reused by another team or partner
