/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    serverActions: true
  },
  env: {
    BACKEND_URL: process.env.BACKEND_URL || "http://localhost:8000"
  }
};

export default nextConfig;

