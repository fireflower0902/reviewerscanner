import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: '*.reviewnote.co.kr',
      },
      {
        protocol: 'https',
        hostname: '*.xn--939au0g4vj8sq.net', // 강남맛집 (subdomains might exist)
      },
      {
        protocol: 'https',
        hostname: 'xn--939au0g4vj8sq.net', // 강남맛집
      },
      {
        protocol: 'https',
        hostname: 'gangnam-review.net', // 강남맛집 이미지 서버
      },
      {
        protocol: 'https',
        hostname: 'www.reviewplace.co.kr', // 리뷰플레이스
      },
      {
        protocol: 'https',
        hostname: 'cdn.cdnreviewplace.co.kr', // 리뷰플레이스 CDN
      },
      {
        protocol: 'https',
        hostname: 'firebasestorage.googleapis.com', // 리뷰노트 등 추가 이미지 소스
      },
      {
        protocol: 'https',
        hostname: 'dq-files.gcdn.ntruss.com', // 디너의여왕 이미지 서버
      },
      {
        protocol: 'https',
        hostname: 'www.seoulouba.co.kr', // 서울오빠 이미지 서버
      },
      {
        protocol: 'https',
        hostname: '*.weble.net', // 레뷰 이미지 서버
      },
      {
        protocol: 'https',
        hostname: 'www.cometoplay.kr', // 놀러와체험단 이미지 서버
      },
      {
        protocol: 'https',
        hostname: 'd3oxv6xcx9d0j1.cloudfront.net', // 포블로그 이미지 서버
      },
      {
        protocol: 'https',
        hostname: 'www.ohmyblog.co.kr', // 오마이블로그 이미지 서버
      }
    ],
  },
};

export default nextConfig;
