# Ralph Backend Reports

This folder stores timestamped artifacts from the local Ralph backend review loop.

Expected runtime layout:

- `runs/<timestamp>/flattened-backend.txt`
- `runs/<timestamp>/review.md`
- `runs/<timestamp>/meta.json`
- `latest/flattened-backend.txt`
- `latest/review.md`
- `latest/meta.json`

Start the loop from the repo root:

```bash
scripts/ralph-backend-loop.sh --interval-minutes 15
```

Run a single review cycle:

```bash
scripts/ralph-backend-loop.sh --once
```

Start it in the background:

```bash
scripts/ralph-backend-loop.sh --background --interval-minutes 15
```

The first implementation is review-only. It does not patch backend source files automatically.
