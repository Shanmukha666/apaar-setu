import type { NextConfig } from "next";

// cacheComponents / partialPrefetching were removed: they keep previously visited pages mounted (hidden), so route
// guards on hidden pages fire stale redirects after logout. The prototype does not need them.
const nextConfig: NextConfig = {
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
