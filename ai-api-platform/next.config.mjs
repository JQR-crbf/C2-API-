/** @type {import('next').NextConfig} */
const nextConfig = {
  eslint: {
    ignoreDuringBuilds: true,
  },
  typescript: {
    ignoreBuildErrors: true,
  },
  images: {
    unoptimized: true,
  },
  // 只在开发环境使用 rewrites，生产环境通过环境变量配置后端地址
  async rewrites() {
    if (process.env.NODE_ENV === 'development') {
      // 临时指向 Railway 后端进行测试
      return [
        {
          source: '/api/:path*',
          destination: 'https://c2-api-production.up.railway.app/api/:path*',
        },
      ]
    }
    return []
  },
}

export default nextConfig
