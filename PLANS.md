# PLANS.md

## Current milestone

Stage 0: scaffold the hackathon repo

## Planning mode

Detailed feature planning is intentionally deferred until hackathon day.

Until then:

- keep the repo ready for rapid execution
- avoid locking in feature scope too early
- favor scaffolding, context, and reusable setup over speculative implementation

Hackathon-day runbook:

- `docs/hackathon-runbook.md`

## Tasks

- [x] Create repo-managed skill base
- [x] Add local Codex skill sync script
- [x] Initialize git remote
- [x] Add Stage 0 repo docs and instructions
- [x] Scaffold frontend shell
- [x] Scaffold API shell
- [x] Scaffold orchestrator shell
- [x] Scaffold context graph shell
- [x] Install bootstrap dependencies
- [x] Add local startup scripts
- [x] Add environment templates

## Exit criteria

- Repo structure exists
- Dependencies are installed
- Frontend shell is installed and lint-validated
- API shell runs
- Orchestrator shell runs
- Context graph shell runs
- Startup instructions are documented

## Judging checklist

Use this rubric to evaluate ideas and demo choices on hackathon day:

- `25%` Depth of Codex integration
  Refine as: evaluate how central Codex is to the solution and how meaningfully it is used across the build and runtime workflow.
  Strong entries show Codex as a core driver of development, including generating, iterating, debugging, and improving code through agentic workflows, not just as an assistive tool.
- `25%` Real-world partner impact
  Refine as: evaluate how directly the project addresses a meaningful internal partner problem or customer-facing opportunity.
  Strong entries solve clear, practical challenges in delivery, engineering, implementation, or go-to-market contexts, with a well-defined user and a credible real-world application.
- `25%` Reusability and adoption potential
  Refine as: evaluate the long-term value of the project beyond the hackathon.
  Strong entries demonstrate clear potential to be reused, scaled, or productized as a partner accelerator, internal tool, customer offering, or Codex-embedded aid to a repeatable workflow or delivery motion.
- `25%` Demo and pitch quality
  Refine as: evaluate how clearly and effectively the team communicates the solution and its value.
  Strong entries present a compelling end-to-end narrative covering the problem, what was built, why it matters, and how Codex was used throughout the process.

For the final demo, show both the outcome and the workflow:

- what we built
- why it matters
- where Codex accelerated or transformed the build

## Delivery constraints

- total hackathon time is `4h`
- team size is `3` people
- submission includes a `1 min` recorded video, for example via Loom
- the video should explain what was built and why
- judging includes `3 mins` of live demo plus `1-2 mins` of Q&A
- live demo quality is critical to scoring
- the live demo must be a working product flow, not a slide deck, PDF, or HTML-only explanation

## Next milestone

Stage 1: semantic mapping golden path
