import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // shiki uses WASM — needs to be treated as server-only
  serverExternalPackages: ["shiki"],
};

export default nextConfig;
