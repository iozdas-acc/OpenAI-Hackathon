# AGENTS.md

## Purpose

This repository builds a human-in-the-loop semantic translation platform for business ontology mapping.

## Hackathon judging context

Optimize decisions, scope, and storytelling for the judging criteria:

- `25%` Depth of Codex integration
- `25%` Real-world partner impact
- `25%` Reusability and adoption potential
- `25%` Demo and pitch quality

For demos and implementation choices, show both the outcome and the workflow:

- what was built
- why it matters
- where Codex accelerated or transformed the build

Read these files before making structural or architectural decisions:

- `docs/architecture.md`
- `docs/iterations.md`
- `docs/ontology-model.md`
- `docs/skills-inventory.md`
- `PLANS.md`

## Stage policy

Build in explicit stages.

### Stage 0

Scaffolding only:

- repo structure
- docs
- app shells
- dependency installation
- local scripts
- env templates
- skill setup

No product features.

### Stage 1

One semantic mapping golden path from raw field to approved ontology concept.

### Stage 2

Live context graph updates.

### Stage 3

Business dictionary output.

### Stage 4

Migration planning stub.

## Architecture rules

- Frontend is an enterprise dashboard with gamified elements.
- LangGraph is the orchestration backbone.
- Keep LangChain usage optional and inside the orchestrator service only when it simplifies integration.
- Prefer Postgres as the primary durable store.
- Keep Web3D and heavier frontend effects optional and demo-driven, not mandatory for the first vertical slice.

## Implementation rules

- Prefer the smallest working scaffold first.
- Keep diffs small.
- Update `PLANS.md` when stage scope changes.
- Keep frontend, API, orchestration, and graph logic separated.
- Repo-managed skills are the source of truth; local Codex installs are symlinked from the repo.
- Prefer native Codex tools, local repo scripts, and repo-managed skills over external agent CLIs or vendor-specific workflows when an equivalent exists here.

## Skill routing

Choose skills by folder category first, then pick the smallest set of skills that matches the task.

- `skills/planning/`
  - Use for design, ideation, feature shaping, or behavior changes before implementation.
  - `brainstorming` is the required first step for creative or behavior-changing work.
- `skills/repo/`
  - Use for repository scaffolding, shared docs, local helper scripts, skill authoring, and skill maintenance.
  - Default to `repo-bootstrap` for repo setup and `skill-creator` for creating or updating skills.
- `skills/frontend/design/`
  - Use for visual direction, layout, styling, and experience design work.
- `skills/frontend/web2d/`
  - Use for React, Next.js, composition, performance, and general web UI implementation or review.
- `skills/frontend/audits/`
  - Use for focused accessibility, usability, and standards audits or refactors.
- `skills/frontend/motion/`
  - Use for GSAP and motion-heavy interaction work.
- `skills/frontend/web3d/`
  - Use for Three.js, React Three Fiber, shaders, post-processing, or 3D interaction work.
- `skills/hackathon/`
  - Use for repo-specific stage gates, scoring optimization, orchestration structure, and semantic translation platform guidance.

When multiple skills apply, use them in this order unless the task clearly requires a different sequence:

1. stage and repo constraints
2. planning
3. implementation
4. audit or review

Skill usage rules:

- Prefer the repo copy under `skills/` over any local or system-installed copy of the same skill.
- If an imported skill mentions tools that do not exist in this Codex environment, adapt the workflow to the available Codex tool surface instead of following the external instructions literally.
- Do not install a duplicate external skill when the repo already contains an equivalent or adapted version.

## Verification rules

- Every completed scaffold task should leave the repo more runnable or more understandable.
- For Stage 0, validation means the shells install, start, or document a clear startup path.
