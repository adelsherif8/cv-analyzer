/** @type {import('next').NextConfig} */
const nextConfig = {
  // pdf-parse + mammoth use Node internals / dynamic requires — keep them as
  // external runtime deps so webpack doesn't mangle them in the server bundle.
  experimental: {
    serverComponentsExternalPackages: ['mammoth'],
  },
  eslint: {
    ignoreDuringBuilds: true,
  },
  typescript: {
    ignoreBuildErrors: true,
  },
}

module.exports = nextConfig
