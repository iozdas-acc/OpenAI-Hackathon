# Skill Inventory

This repo vendors a first-pass skill base for the hackathon project. The repo copy is the source of truth. Local Codex access is handled by `scripts/sync-codex-skills.sh`.

## Categories

### Planning

- `brainstorming`

### Frontend / Design

- `frontend-design`
- `bencium-controlled-ux-designer`
- `bencium-innovative-ux-designer`

### Frontend / Web2D

- `composition-patterns`
- `react-best-practices`
- `react-best-practices-vercel`
- `web-design-guidelines`

### Frontend / Web3D

- `react-three-fiber`
- `r3f-animation`
- `r3f-fundamentals`
- `r3f-geometry`
- `r3f-interaction`
- `r3f-lighting`
- `r3f-materials`
- `r3f-postprocessing`
- `r3f-shaders`
- `threejs-webgl`
- `web3d-integration-patterns`

### Frontend / Motion

- `gsap-scrolltrigger`

### Frontend / Audits

- `accesslint-refactor`
- `contrast-checker`
- `link-purpose`
- `use-of-color`

### Repo

- `repo-bootstrap`
- `skill-creator`

### Hackathon

- `langgraph-runtime`
- `iteration-stage-gate`

## Portability

### Portable or light-adapt

- `brainstorming`
- `skill-creator`
- all imported design, web2d, web3d, and motion skills
- `link-purpose`
- `use-of-color`

### Needs adaptation

- `contrast-checker`
  - references MCP tools that are not currently available in this Codex environment
- `accesslint-refactor`
  - references tool names that should be verified against the current Codex tool surface before relying on automated refactors

### Deferred

- `gstack` and related Claude workflow skills
- plain guide-only folders that do not yet have `SKILL.md`

## Team Usage

1. Clone the repo.
2. Run `scripts/sync-codex-skills.sh`.
3. Restart Codex.

Do not commit local symlinks. Commit the actual skill folders under `skills/`.

## Selection Guidance

Treat the folder structure as the first routing layer when deciding which skill to use.

- `skills/planning/` for design and requirement shaping
- `skills/repo/` for repo setup, shared docs, scripts, and skill authoring
- `skills/frontend/design/` for visual design work
- `skills/frontend/web2d/` for React, Next.js, and web UI patterns
- `skills/frontend/audits/` for accessibility and UX audits
- `skills/frontend/motion/` for GSAP and motion work
- `skills/frontend/web3d/` for Three.js and R3F work
- `skills/hackathon/` for stage-gated hackathon-specific architecture rules

Prefer repo-managed skills and native Codex tools first. Treat imported vendor workflows as reference material that should be adapted to the current Codex tool surface.
