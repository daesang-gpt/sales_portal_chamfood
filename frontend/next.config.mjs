/** @type {import('next').NextConfig} */
const nextConfig = {
  // 외부 IP 접속 허용을 위한 설정
  experimental: {
    // 외부 네트워크에서 접속 허용
    serverComponentsExternalPackages: [],
  },
  // 개발 서버 설정
  devIndicators: {
    buildActivity: true,
  },
  // 이미지 최적화 설정
  images: {
    domains: [],
    unoptimized: false,
  },
  // 환경 변수 설정
  env: {
    CUSTOM_KEY: 'my-value',
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