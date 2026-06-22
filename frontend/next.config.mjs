/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // The web app is a pure client of the FastAPI backend (ADR-0002). The API base URL is
  // injected per-environment via NEXT_PUBLIC_API_BASE_URL (see .env.example); no API
  // hostnames are hard-coded. Real rewrites/headers/CSP land at Phase F.

  // Standalone output: `next build` emits a self-contained `.next/standalone/` tree (a minimal
  // node server + only the deps it actually imports). The frontend Dockerfile copies that tree
  // into a slim runtime image and runs `node server.js`, which is what Cloud Run needs — a small
  // stateless container that binds the platform-provided $PORT. (NEXT_PUBLIC_API_BASE_URL is a
  // build-time inline for NEXT_PUBLIC_* vars, so it is baked at `docker build`, not at runtime.)
  output: "standalone",
};

export default nextConfig;
