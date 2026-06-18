/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // The web app is a pure client of the FastAPI backend (ADR-0002). The API base URL is
  // injected per-environment via NEXT_PUBLIC_API_BASE_URL (see .env.example); no API
  // hostnames are hard-coded. Real rewrites/headers/CSP land at Phase F.
};

export default nextConfig;
