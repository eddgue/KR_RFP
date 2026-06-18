// Landing stub (Phase 0/A). Built last (ADR-0002); this page exists only to PROVE the API
// seam — it calls the backend /health endpoint so the store<->view boundary is real from day one.
// At Phase F this is replaced by the real console; types come from the OpenAPI contract (lib/api/).

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

type HealthState =
  | { status: "ok"; payload: unknown }
  | { status: "down"; detail: string };

// Server Component: fetches once on render. No caching so the seam reflects live backend state.
async function probeHealth(): Promise<HealthState> {
  try {
    const res = await fetch(`${API_BASE_URL}/health`, { cache: "no-store" });
    if (!res.ok) {
      return { status: "down", detail: `HTTP ${res.status}` };
    }
    return { status: "ok", payload: await res.json() };
  } catch (err) {
    return {
      status: "down",
      detail: err instanceof Error ? err.message : "unreachable",
    };
  }
}

export default async function Page() {
  const health = await probeHealth();

  return (
    <main style={{ maxWidth: 720, margin: "4rem auto", padding: "0 1.5rem" }}>
      <h1>KR_RFP Console</h1>
      <p style={{ color: "#555" }}>
        Placeholder client. The enterprise web app is built last (Phase F, ADR-0002).
        This page exists to prove the API seam.
      </p>

      <section
        style={{
          marginTop: "2rem",
          padding: "1rem 1.25rem",
          borderRadius: 8,
          border: "1px solid #e2e2e2",
          background: health.status === "ok" ? "#f3fbf4" : "#fdf3f3",
        }}
      >
        <h2 style={{ marginTop: 0 }}>Backend /health</h2>
        <p>
          Target: <code>{API_BASE_URL}/health</code>
        </p>
        {health.status === "ok" ? (
          <pre style={{ overflowX: "auto" }}>
            {JSON.stringify(health.payload, null, 2)}
          </pre>
        ) : (
          <p style={{ color: "#a33" }}>
            Backend unreachable ({health.detail}). Start it with{" "}
            <code>docker compose up</code> in <code>infra/</code>.
          </p>
        )}
      </section>
    </main>
  );
}
