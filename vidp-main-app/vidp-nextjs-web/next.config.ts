import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  output: 'standalone',
  // Configuration pour Docker
  experimental: {
    // Optimisations pour Docker
  },
};

export default nextConfig;
