/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",

  // Proxy API calls from the frontend to the backend.
  // Client-side fetch uses NEXT_PUBLIC_API_URL (http://localhost:8000).
  // SSR rewrites route through the backend URL.
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${process.env.BACKEND_INTERNAL_URL || "http://localhost:8000"}/api/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;

