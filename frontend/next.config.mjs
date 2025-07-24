/** @type {import('next').NextConfig} */
const nextConfig = {
  // 외부 IP 접속 허용을 위한 설정
  serverExternalPackages: [],
  // 이미지 최적화 설정
  images: {
    domains: [],
    unoptimized: true, // 개발 환경에서 최적화 비활성화
  },
  // 환경 변수 설정
  env: {
    CUSTOM_KEY: 'my-value',
  },
  // 개발 환경 최적화 설정
  experimental: {
    // 파일 시스템 오류 방지
    optimizePackageImports: [],
  },
  // 웹팩 설정 최적화
  webpack: (config, { dev, isServer }) => {
    if (dev) {
      // 개발 환경에서 파일 시스템 오류 방지
      config.watchOptions = {
        poll: 1000,
        aggregateTimeout: 300,
        ignored: ['**/node_modules', '**/.next'],
      };
      
      // Windows 환경에서 파일 경로 문제 해결
      config.resolve.fallback = {
        ...config.resolve.fallback,
        fs: false,
        path: false,
      };
    }
    return config;
  },
  // 헤더 설정
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          {
            key: 'X-Frame-Options',
            value: 'DENY',
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff',
          },
        ],
      },
    ];
  },
};

export default nextConfig;