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
    // Windows 환경에서 파일 시스템 오류 방지
    esmExternals: 'loose',
  },
  // Windows 환경에서 파일 시스템 오류 방지를 위한 설정
  outputFileTracingIncludes: {},
  outputFileTracingExcludes: {},
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
        os: false,
      };
      
      // 파일 시스템 오류 방지를 위한 추가 설정
      config.infrastructureLogging = {
        level: 'error',
      };
      
      // Windows 환경에서 파일 읽기/쓰기 오류 방지
      config.optimization = {
        ...config.optimization,
        moduleIds: 'deterministic',
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