"use client";

import { useEffect, useMemo, useState } from "react";

type BackendProbe = {
  backendUrl: string;
  checkedAt: string;
  latencyMs: number;
  payload: { status?: string } | null;
  ok: boolean;
  status: number;
};

type ProbeState = {
  data: BackendProbe | null;
  error: string | null;
  loading: boolean;
};

const evidenceSignals = [
  "Field embeddings converge around customer segmentation semantics.",
  "Reference graph expands as cross-company entity neighbors line up.",
  "Ontology candidate confidence lifts when synonym clusters stabilize.",
];

const eventSnapshots = [
  "Company A: `customer_tier` enters the semantic lane.",
  "Company B: `client_segment` resolves against the same concept family.",
  "Shared graph writes new edges across account, contract, and region nodes.",
  "AI proposes `Customer Classification` for review.",
];

async function loadProbe(): Promise<BackendProbe> {
  const response = await fetch("/api/backend/health", { cache: "no-store" });
  const data = (await response.json()) as BackendProbe & { error?: string };

  if (!response.ok) {
    throw new Error(data.error ?? "Backend probe failed.");
  }

  return data;
}

export function LayeredWaveDemo() {
  const [probeState, setProbeState] = useState<ProbeState>({
    data: null,
    error: null,
    loading: true,
  });
  const [activeSignal, setActiveSignal] = useState(0);
  const [eventCursor, setEventCursor] = useState(0);

  useEffect(() => {
    let cancelled = false;

    const runProbe = async () => {
      setProbeState((current) => ({ ...current, loading: true, error: null }));

      try {
        const data = await loadProbe();
        if (cancelled) {
          return;
        }

        setProbeState({ data, error: null, loading: false });
      } catch (error) {
        if (cancelled) {
          return;
        }

        const message =
          error instanceof Error ? error.message : "Backend probe failed.";
        setProbeState((current) => ({
          data: current.data,
          error: message,
          loading: false,
        }));
      }
    };

    void runProbe();
    const timer = window.setInterval(() => {
      void runProbe();
    }, 5000);

    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, []);

  useEffect(() => {
    const signalTimer = window.setInterval(() => {
      setActiveSignal((current) => (current + 1) % evidenceSignals.length);
    }, 2400);

    const eventTimer = window.setInterval(() => {
      setEventCursor((current) => (current + 1) % eventSnapshots.length);
    }, 1800);

    return () => {
      window.clearInterval(signalTimer);
      window.clearInterval(eventTimer);
    };
  }, []);

  const backendBadge = useMemo(() => {
    if (probeState.loading && !probeState.data) {
      return { label: "Connecting", tone: "is-neutral" };
    }

    if (probeState.error) {
      return { label: "Backend Unreachable", tone: "is-danger" };
    }

    if (probeState.data?.ok) {
      return { label: "Backend Live", tone: "is-success" };
    }

    return { label: "Probe Pending", tone: "is-neutral" };
  }, [probeState.data, probeState.error, probeState.loading]);

  return (
    <main className="demo-shell">
      <section className="demo-hero">
        <div className="partner-bar">
          <div>
            <span className="eyebrow">Semantic Translation Platform</span>
            <h1>Layered wave mapping for a two-database ontology merge.</h1>
          </div>
          <div className="partner-lockup" aria-label="OpenAI and Accenture partner treatment">
            <span>OpenAI</span>
            <i />
            <span>Accenture</span>
          </div>
        </div>

        <div className="hero-grid">
          <aside className="glass-panel evidence-panel">
            <div className="panel-header">
              <span className="panel-kicker">Semantic Evidence</span>
              <span className={`status-pill ${backendBadge.tone}`}>{backendBadge.label}</span>
            </div>
            <ul className="signal-list">
              {evidenceSignals.map((signal, index) => (
                <li
                  key={signal}
                  className={index === activeSignal ? "signal-card is-active" : "signal-card"}
                >
                  {signal}
                </li>
              ))}
            </ul>
            <div className="schema-stack">
              <div className="schema-card">
                <strong>Company A</strong>
                <span>`customer_tier`</span>
                <span>`acct_status`</span>
                <span>`region_group`</span>
              </div>
              <div className="schema-card">
                <strong>Company B</strong>
                <span>`client_segment`</span>
                <span>`portfolio_band`</span>
                <span>`market_motion`</span>
              </div>
            </div>
          </aside>

          <section className="graph-stage glass-panel">
            <div className="panel-header">
              <span className="panel-kicker">Layered Wave Engine</span>
              <span className="micro-copy">
                Schema {"->"} semantics {"->"} graph {"->"} ontology
              </span>
            </div>

            <div className="graph-canvas" aria-hidden="true">
              <div className="wave-layer wave-layer-a" />
              <div className="wave-layer wave-layer-b" />
              <div className="wave-layer wave-layer-c" />

              <div className="graph-link link-a" />
              <div className="graph-link link-b" />
              <div className="graph-link link-c" />

              <div className="graph-node node-a" />
              <div className="graph-node node-b" />
              <div className="graph-node node-c" />
              <div className="graph-node node-d" />
              <div className="graph-node node-e" />
              <div className="graph-node node-f" />

              <div className="graph-badge badge-a">schema layer</div>
              <div className="graph-badge badge-b">semantic layer</div>
              <div className="graph-badge badge-c">ontology layer</div>
            </div>

            <div className="event-rail" aria-live="polite">
              {eventSnapshots.map((event, index) => (
                <div
                  key={event}
                  className={index === eventCursor ? "event-card is-current" : "event-card"}
                >
                  {event}
                </div>
              ))}
            </div>
          </section>

          <aside className="glass-panel outcome-panel">
            <div className="panel-header">
              <span className="panel-kicker">Proposed Ontology</span>
              <span className="confidence-pill">0.93 confidence</span>
            </div>

            <div className="ontology-card">
              <p>Candidate concept</p>
              <h2>Customer Classification</h2>
              <span>Shared business meaning discovered across both company datasets.</span>
            </div>

            <div className="approval-card">
              <div>
                <strong>Human checkpoint</strong>
                <p>Review remains visible so judges see control, not blind automation.</p>
              </div>
              <button type="button">Approve mapping</button>
            </div>

            <div className="probe-card">
              <div className="probe-header">
                <strong>Backend probe</strong>
                <button
                  type="button"
                  onClick={() => {
                    setProbeState((current) => ({ ...current, loading: true }));
                    void loadProbe()
                      .then((data) => {
                        setProbeState({ data, error: null, loading: false });
                      })
                      .catch((error: unknown) => {
                        const message =
                          error instanceof Error
                            ? error.message
                            : "Backend probe failed.";
                        setProbeState((current) => ({
                          data: current.data,
                          error: message,
                          loading: false,
                        }));
                      });
                  }}
                >
                  Refresh
                </button>
              </div>

              <dl className="probe-grid">
                <div>
                  <dt>Endpoint</dt>
                  <dd>{probeState.data?.backendUrl ?? "Waiting for probe..."}</dd>
                </div>
                <div>
                  <dt>Latency</dt>
                  <dd>
                    {probeState.data ? `${probeState.data.latencyMs} ms` : "--"}
                  </dd>
                </div>
                <div>
                  <dt>Status</dt>
                  <dd>{probeState.data?.payload?.status ?? probeState.error ?? "--"}</dd>
                </div>
                <div>
                  <dt>Checked</dt>
                  <dd>
                    {probeState.data
                      ? new Date(probeState.data.checkedAt).toLocaleTimeString()
                      : "--"}
                  </dd>
                </div>
              </dl>
            </div>
          </aside>
        </div>
      </section>
    </main>
  );
}
