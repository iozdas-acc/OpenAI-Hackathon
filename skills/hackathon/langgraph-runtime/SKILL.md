---
name: langgraph-runtime
description: Build the LangGraph orchestration runtime for the semantic translation platform. Use when defining graph nodes, state shape, agent responsibilities, transitions, human checkpoints, or iteration-safe runtime structure in the orchestrator service.
---

# LangGraph Runtime

Use this skill when working on the orchestration backbone of the product.

## Purpose

Design and implement a durable LangGraph workflow for:

- schema intake
- semantic extraction
- candidate mapping
- human clarification
- context graph updates
- dictionary generation

## Architecture Rules

- LangGraph belongs in the orchestration service, not in the frontend.
- Prefer explicit state and deterministic transitions over hidden agent behavior.
- Use human checkpoints when confidence is low or ambiguity is high.
- Keep node responsibilities narrow.

## Initial Node Set

- ingest-source-schema
- profile-schema
- extract-semantics
- propose-mappings
- request-human-clarification
- persist-approved-mapping
- update-context-graph
- emit-ui-event

## Iteration Rules

- Stage 0: shell only, no real workflow logic.
- Stage 1: one end-to-end golden path for a small sample schema.
- Do not add extra nodes unless they directly support the current stage exit criteria.
