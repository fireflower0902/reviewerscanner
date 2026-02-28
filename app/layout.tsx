import type { Metadata } from "next";
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

export const metadata: Metadata = {
  title: "리뷰어 스캐너 | 모든 체험단을 한눈에",
  description: "모든 체험단을 한눈에. 지역별, 보상별 맞춤 검색으로 최적의 체험단 캠페인을 찾아보세요.",
  openGraph: {
    title: "리뷰어 스캐너",
    description: "모든 체험단을 한눈에. 지역별, 보상별 맞춤 검색.",
    siteName: "리뷰어 스캐너",
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
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        {children}
      </body>
    </html>
  );
}
