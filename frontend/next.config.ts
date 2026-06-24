import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  reactCompiler: true,
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://backend:8000/api/:path*',
      },
      {
        source: '/auth/:path*',
        destination: 'http://backend:8000/auth/:path*',
      },
      {
        source: '/health',
        destination: 'http://backend:8000/health',
      },
    ];
  },
};

export default nextConfig;
