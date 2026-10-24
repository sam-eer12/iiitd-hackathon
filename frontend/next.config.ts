import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  distDir: process.env.NODE_ENV === "production" ? ".next-production" : ".next",
  redirects() {
    if (process.env.NODE_ENV !== "development") return [];

    // Firebase authorizes localhost for Google sign-in, not the loopback IP.
    // Redirect browser navigation while keeping API and asset requests intact.
    return [
      {
        source: "/:path*",
        has: [
          { type: "host", value: "127\\.0\\.0\\.1" },
          { type: "header", key: "accept", value: ".*text/html.*" },
        ],
        destination: `http://localhost:${process.env.PORT || "3000"}/:path*`,
        permanent: false,
      },
    ];
  },
  experimental: {
    agentFeedback: true,
  },
  cacheComponents: true,
  partialPrefetching: true,
  turbopack: {
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
};

export default nextConfig;
