import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    // In production (Vercel), NEXT_PUBLIC_BACKEND_URL must be set to your Render backend URL.
    // e.g. https://your-app-name.onrender.com
    // In local development it falls back to localhost:8000.
    const backendUrl =
      process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

    return [
      {
        source: "/api/:path*",
        destination: `${backendUrl}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
