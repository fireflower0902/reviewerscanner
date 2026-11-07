'use client';

import { useEffect, useRef, useState } from 'react';
import { Menu, Share2 } from 'lucide-react';
import { useFilterDrawer } from './FilterDrawer';
import { useShare, ShareToast } from './ShareButton';

/**
 * 상단 파란 제목 영역.
 *  - 모바일/태블릿(사이드바가 서랍인 화면): 맨 위에서는 제목 줄 오른쪽 끝에 하늘색 '필터' 버튼이 있다.
 *    스크롤을 내려 제목이 화면 밖으로 나가면, 하얀 바탕의 얇은 띠에 '필터' 버튼만 화면 위에 고정된다.
 *  - PC: 사이드바가 항상 보이므로 필터 버튼과 고정 띠가 없다.
 *  - 제목 줄 오른쪽 끝에는 '공유' 버튼이 있다 (모바일은 기본 공유 창, PC는 링크 복사).
 */
export default function Hero() {
    const { setOpen } = useFilterDrawer();
    const { share, toast } = useShare();
    const topButtonRef = useRef<HTMLButtonElement>(null);
    const [scrolledPast, setScrolledPast] = useState(false);   // 제목 줄의 필터 버튼이 화면 위로 올라가 사라졌는가

    // 제목 줄의 버튼이 화면 밖(위쪽)으로 나가는 순간 하얀 고정 띠를 보여준다 — 버튼이 없는 구간이 생기지 않는다
    // (PC에서는 버튼이 display:none 이라 항상 false)
    useEffect(() => {
        const el = topButtonRef.current;
        if (!el) return;
        const io = new IntersectionObserver(
            ([entry]) => setScrolledPast(!entry.isIntersecting && entry.boundingClientRect.top < 0),
            // 위쪽 2px를 안쪽으로 줄여, 버튼이 화면 가장자리에 정확히 걸치는 한 지점에서도 빈 구간이 생기지 않게 한다
            { threshold: 0, rootMargin: '-2px 0px 0px 0px' }
        );
        io.observe(el);
        return () => io.disconnect();
    }, []);

    return (
        <>
            <div
                className="bg-gradient-to-r from-blue-600 to-indigo-700 text-white px-4 overflow-visible flex flex-col items-center justify-center pt-2 pb-2 md:pt-4 md:pb-0"
            >
                {/* 제목 줄만 기준점(relative)으로 삼아 필터 버튼을 왼쪽 끝에 둔다 */}
                <div className="relative w-full">
                    <div className="max-w-7xl mx-auto text-center">
                        <h1 className="text-2xl md:text-3xl font-extrabold tracking-tight mb-1 md:mb-2">
                            체험단 스캐너
                        </h1>
                        {/* 모바일에서는 설명 문구 숨김 */}
                        <p className="hidden md:block text-sm md:text-base text-blue-100 max-w-2xl mx-auto">
                            블로그 체험단 사이트 모음, 체험단 스캐너. 지역·보상별로 한눈에 찾아보세요.
                        </p>
                    </div>

                    {/* 맨 위에서의 필터 버튼 — 파란 배경 위의 반투명 유리 느낌 */}
                    <button
                        ref={topButtonRef}
                        type="button"
                        onClick={() => setOpen(true)}
                        className="lg:hidden absolute left-0 top-0 z-10 flex items-center gap-1.5 px-3 py-1.5 bg-white/20 text-white border border-white/50 hover:bg-white/30 active:bg-white/40 backdrop-blur-sm rounded-lg text-sm font-bold shadow-md transition-colors"
                    >
                        <Menu size={16} />
                        필터
                    </button>

                    {/* 공유하기 — 제목 줄 오른쪽 끝 (PC·모바일 공통) */}
                    <button
                        type="button"
                        onClick={share}
                        aria-label="사이트 공유하기"
                        className="absolute right-0 top-0 z-10 flex items-center gap-1.5 px-3 py-1.5 bg-white/20 text-white border border-white/50 hover:bg-white/30 active:bg-white/40 backdrop-blur-sm rounded-lg text-sm font-bold shadow-md transition-colors"
                    >
                        <Share2 size={16} />
                        공유
                    </button>
                </div>
            </div>

            {/* 스크롤 후: 하얀 바탕에 필터 버튼만 고정 (서랍 z-50·어두운 배경 z-40보다 아래) */}
            {scrolledPast && (
                <div className="lg:hidden fixed top-0 left-0 right-0 z-30 bg-white border-b border-gray-200 shadow-sm">
                    <div className="flex items-center justify-between px-4 py-1.5">
                        <button
                            type="button"
                            onClick={() => setOpen(true)}
                            className="flex items-center gap-1.5 px-3 py-1.5 bg-blue-600 text-white hover:bg-blue-700 active:bg-blue-800 rounded-lg text-sm font-bold shadow-sm transition-colors"
                        >
                            <Menu size={16} />
                            필터
                        </button>
                        <button
                            type="button"
                            onClick={share}
                            aria-label="사이트 공유하기"
                            className="flex items-center gap-1.5 px-3 py-1.5 border border-gray-300 text-gray-700 hover:bg-gray-50 active:bg-gray-100 rounded-lg text-sm font-bold transition-colors"
                        >
                            <Share2 size={16} />
                            공유
                        </button>
                    </div>
                </div>
            )}

            <ShareToast message={toast} />
        </>
    );
}
