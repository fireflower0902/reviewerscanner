import type { Metadata, Viewport } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

// 폰 브라우저 위쪽 줄 색(앱으로 설치했을 때 상태바 색도 이 색을 따른다)
export const viewport: Viewport = {
  themeColor: "#2563eb",
};

export const metadata: Metadata = {
  // 홈 화면에 앱처럼 설치(PWA) — 이름·아이콘·전체 화면 실행 정보
  manifest: "/manifest.webmanifest",
  appleWebApp: { capable: true, title: "체험단 스캐너", statusBarStyle: "default" },
  // og:image 등 상대 경로를 절대 주소로 바꾸는 기준 (미설정 시 http://localhost:3000 으로 만들어져 카카오·SNS 미리보기 이미지가 안 뜬다)
  metadataBase: new URL("https://scan.reviewerscanner.com"),
  // 구글 서치콘솔 소유확인
  verification: {
    google: "PbDI8GCtHYZOMoNM8bIAxJeETS37i6kP3Bfg0dfXbeU",
    other: { "naver-site-verification": "3f97fad74b095247217575e51805cf3010abb016" },
  },
  title: "체험단 스캐너 | 블로그 체험단 사이트 모음",
  description: "블로그 체험단 사이트 모음, 체험단 스캐너. 강남맛집·레뷰·리뷰노트 등 9개 체험단 캠페인을 지역별·보상별로 한눈에 찾아보세요.",
  openGraph: {
    title: "체험단 스캐너 | 블로그 체험단 사이트 모음",
    description: "블로그 체험단 사이트 모음, 체험단 스캐너. 지역·보상별로 한눈에 찾아보세요.",
    siteName: "체험단 스캐너",
    locale: "ko_KR",
    type: "website",
  },
};


export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ko">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        {children}
      </body>
    </html>
  );
}
