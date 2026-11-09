import Link from 'next/link';
import { House } from 'lucide-react';

/** 이용가이드·이용약관 같은 안내 페이지의 공통 틀 (맨 위 로고 줄 + 본문 + 아래 링크) */
export default function InfoPage({
    current,
    title,
    updated,
    children,
}: {
    current: 'guide' | 'terms';
    title: string;
    updated?: string;
    children: React.ReactNode;
}) {
    const navClass = (active: boolean) =>
        `rounded-lg px-3 py-1.5 text-sm font-semibold transition-colors ${active ? 'bg-blue-50 text-blue-700' : 'text-gray-600 hover:bg-gray-50 hover:text-blue-700'}`;
    return (
        <div className="min-h-screen bg-white text-gray-900">
            <header className="border-b border-gray-200 bg-white">
                <div className="mx-auto flex max-w-3xl items-center justify-between gap-3 px-4 py-3">
                    {/* 일반 링크(<a>)라서 누르면 홈이 새로 불러와진다 (선택한 필터도 처음 상태로) */}
                    {/* eslint-disable-next-line @next/next/no-html-link-for-pages */}
                    <a href="/" aria-label="체험단 스캐너 홈 화면으로 가기" className="flex items-center gap-2.5">
                        {/* eslint-disable-next-line @next/next/no-img-element */}
                        <img src="/mascot/bear-lens.svg" alt="" width={36} height={36} className="h-9 w-9 rounded-lg" />
                        <span className="text-lg font-extrabold tracking-tight">체험단 스캐너</span>
                    </a>
                    <nav className="flex items-center gap-1">
                        <Link href="/guide" className={navClass(current === 'guide')}>이용가이드</Link>
                        <Link href="/terms" className={navClass(current === 'terms')}>이용약관</Link>
                    </nav>
                </div>
            </header>

            <main className="mx-auto max-w-3xl px-4 py-8 sm:py-10">
                <HomeButton />
                <h1 className="mt-4 text-2xl font-extrabold tracking-tight sm:text-3xl">{title}</h1>
                {updated && <p className="mt-2 text-sm text-gray-500">{updated}</p>}
                <div className="mt-8 space-y-10 leading-7 text-[15px] text-gray-800">{children}</div>
                <div className="mt-12 border-t border-gray-200 pt-8">
                    <HomeButton />
                </div>
            </main>

            <footer className="border-t border-gray-200 bg-gray-50">
                <div className="mx-auto flex max-w-3xl flex-wrap items-center justify-between gap-2 px-4 py-6 text-sm text-gray-500">
                    <span>© 체험단 스캐너</span>
                    <span className="flex gap-4">
                        <Link href="/guide" className="hover:text-blue-700">이용가이드</Link>
                        <Link href="/terms" className="hover:text-blue-700">이용약관</Link>
                        <Link href="/" className="hover:text-blue-700">홈</Link>
                    </span>
                </div>
            </footer>
        </div>
    );
}

export function Section({ id, title, children }: { id?: string; title: string; children: React.ReactNode }) {
    return (
        <section id={id} className="scroll-mt-6">
            <h2 className="mb-3 text-xl font-bold tracking-tight">{title}</h2>
            <div className="space-y-3">{children}</div>
        </section>
    );
}

export function Note({ children }: { children: React.ReactNode }) {
    return <div className="rounded-xl border border-blue-100 bg-blue-50 px-4 py-3 text-sm leading-6 text-blue-900">{children}</div>;
}

/** 눈에 띄는 '홈 화면으로 가기' 버튼 (페이지 맨 위와 맨 아래에 둔다) */
function HomeButton() {
    return (
        // eslint-disable-next-line @next/next/no-html-link-for-pages
        <a
            href="/"
            className="inline-flex items-center gap-2 rounded-xl bg-blue-600 px-5 py-3 text-base font-bold text-white shadow-md transition-colors hover:bg-blue-700 active:bg-blue-800"
        >
            <House size={18} />
            홈 화면으로 가기
        </a>
    );
}
