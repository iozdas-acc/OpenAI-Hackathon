FastAPI backend for the Codex-native `Understand` workflow.

Current scope:

- create projects
- create source/target database connections
- attach project files
- create `understand` runs
- persist run history locally
- stream run events over SSE
- call Codex through the OpenAI Responses API

## Environment

Required for real Codex runs:

- `OPENAI_API_KEY`

Optional:

- `OPENAI_CODEX_MODEL` default: `gpt-5-codex`
- `OPENAI_BASE_URL` default: `https://api.openai.com/v1`
- `CODEX_STORE_DIR` or `SEMANTIC_API_DATA_DIR` for local persistence
- target Postgres connection settings such as `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`,
  `POSTGRES_USER`, `POSTGRES_PASSWORD`, and optional `POSTGRES_SSLMODE`

## Run

From `apps/api`:

```bash
./.venv/bin/uvicorn main:app --reload
```

## API

### Create project

```bash
curl -X POST http://127.0.0.1:8000/projects \
  -H 'content-type: application/json' \
  -d '{"name":"Acme Migration","description":"Acquired company ontology intake"}'
```

### Attach file

The upload endpoint accepts raw request bytes and reads the filename from `x-filename`.

```bash
curl -X POST http://127.0.0.1:8000/projects/<project_id>/files \
  -H 'x-filename: schema.csv' \
  -H 'content-type: text/csv' \
  --data-binary @schema.csv
```

### Create run

```bash
curl -X POST http://127.0.0.1:8000/projects/<project_id>/runs \
  -H 'content-type: application/json' \
  -d '{"mode":"understand","instructions":"Analyze this schema and infer business meaning."}'
```

### Create database connection

```bash
curl -X POST http://127.0.0.1:8000/projects/<project_id>/connections \
  -H 'content-type: application/json' \
  -d '{"name":"Supabase Target","role":"target","kind":"supabase","config":{}}'
```

### Stream run events

```bash
curl -N http://127.0.0.1:8000/runs/<run_id>/events
```

## Event types

- `run_created`
- `file_attached`
- `codex_started`
- `reasoning_summary`
- `node_created`
- `edge_created`
- `question_raised`
- `confidence_changed`
- `run_completed`
- `run_failed`

If `OPENAI_API_KEY` is missing, runs still persist and terminate with `run_failed` so the UI can
surface the problem cleanly.
