import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // In production, NEXT_PUBLIC_API_URL points to the Railway backend directly.
  // In local dev, rewrites proxy /api/* → localhost:8000 to avoid CORS issues.
  async rewrites() {
    if (process.env.NODE_ENV === "production") return [];
    return [
      {
        source: "/api/:path*",
        destination: `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
