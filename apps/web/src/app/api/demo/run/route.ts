import { access, readFile } from "node:fs/promises";
import path from "node:path";

import { NextResponse } from "next/server";

const DEFAULT_API_URL = "http://localhost:8000";

type StoredRun = {
  id: string;
  status: string;
  created_at: string;
  metadata?: {
    source_connection_id?: string;
    target_connection_id?: string;
  };
};

const STATUS_PRIORITY: Record<string, number> = {
  awaiting_crawl_review: 6,
  awaiting_reasoning_review: 5,
  awaiting_mapping_review: 4,
  migration_ready: 3,
  migration_completed: 2,
  running: 1,
  failed: 0,
};

async function resolveRunsPath(): Promise<string> {
  const candidates = [
    path.resolve(/* turbopackIgnore: true */ process.cwd(), "../api/.data/runs.json"),
    path.resolve(/* turbopackIgnore: true */ process.cwd(), "apps/api/.data/runs.json"),
  ];

  for (const candidate of candidates) {
    try {
      await access(candidate);
      return candidate;
    } catch {
      continue;
    }
  }

  throw new Error("Could not find apps/api/.data/runs.json");
}

function selectDemoRun(runs: StoredRun[]): StoredRun | null {
  const eligible = runs.filter(
    (run) => run.metadata?.source_connection_id && run.metadata?.target_connection_id,
  );
  if (eligible.length === 0) {
    return null;
  }

  return eligible.sort((left, right) => {
    const priorityDelta = (STATUS_PRIORITY[right.status] ?? -1) - (STATUS_PRIORITY[left.status] ?? -1);
    if (priorityDelta !== 0) {
      return priorityDelta;
    }
    return right.created_at.localeCompare(left.created_at);
  })[0];
}

export async function GET(): Promise<Response> {
  try {
    const runsPath = await resolveRunsPath();
    const raw = JSON.parse(await readFile(runsPath, "utf-8")) as Record<string, StoredRun>;
    const selected = selectDemoRun(Object.values(raw));

    if (!selected) {
      return NextResponse.json(
        {
          selectedRunId: null,
          selectionReason: "No demo-ready run with both source and target connections was found.",
          run: null,
          result: null,
          graph: null,
          events: [],
        },
        { status: 404 },
      );
    }

    const backendUrl = process.env.NEXT_PUBLIC_API_URL ?? DEFAULT_API_URL;
    const response = await fetch(`${backendUrl}/runs/${selected.id}`, {
      cache: "no-store",
      signal: AbortSignal.timeout(4000),
    });

    const payload = (await response.json()) as Record<string, unknown>;
    return NextResponse.json(
      {
        selectedRunId: selected.id,
        selectionReason: `Selected the freshest reviewable run in status ${selected.status}.`,
        ...payload,
      },
      { status: response.ok ? 200 : response.status },
    );
  } catch (error) {
    return NextResponse.json(
      {
        selectedRunId: null,
        selectionReason: error instanceof Error ? error.message : "Could not load demo run.",
        run: null,
        result: null,
        graph: null,
        events: [],
      },
      { status: 500 },
    );
  }
}
