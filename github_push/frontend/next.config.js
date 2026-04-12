/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'export',      // static export for Docker / Hugging Face
  trailingSlash: true,
  images: { unoptimized: true },
}

module.exports = nextConfig
