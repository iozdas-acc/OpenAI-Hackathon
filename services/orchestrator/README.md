Codex-backed orchestration layer for semantic translation workflows.

Current implementation:

- one workflow entrypoint: `run_understand_workflow`
- OpenAI Responses API call with structured JSON output
- file-context prompt assembly from uploaded project files
- graph/result normalization for the API layer

LangGraph is intentionally not in the critical path for this first backend slice. The workflow
boundary is set up so LangGraph can be introduced behind the same interface later.
