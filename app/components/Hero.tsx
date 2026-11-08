'use client';

import { useEffect, useRef, useState } from 'react';
import { Menu, Share2 } from 'lucide-react';
import { useFilterDrawer } from './FilterDrawer';
import { useShare, ShareToast } from './ShareButton';
import OverflowMenu from './OverflowMenu';

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
                className="bg-white text-gray-900 border-b border-gray-200 px-4 overflow-visible flex flex-col items-stretch justify-center py-2.5 lg:px-6 lg:py-3"
            >
                {/* 제목 줄만 기준점(relative)으로 삼아 필터 버튼을 왼쪽 끝에 둔다 */}
                <div className="relative w-full">
                    <div className="max-w-7xl mx-auto flex items-center justify-center gap-2 lg:mx-0 lg:justify-start lg:gap-3">
                        {/* PC 전용: 곰돋보기 마스코트 아이콘 */}
                        <img src="/mascot/bear-lens.svg" alt="" width={44} height={44} className="h-9 w-9 shrink-0 rounded-lg lg:h-11 lg:w-11 lg:rounded-xl" />
                        <div>
                            <h1 className="text-xl font-extrabold tracking-tight lg:text-2xl">
                                체험단 스캐너
                            </h1>
                            {/* 화면에는 보이지 않지만(스크린리더용) 소개 문구는 유지 */}
                            <p className="sr-only">
                                블로그 체험단 사이트 모음, 체험단 스캐너. 지역·보상별로 한눈에 찾아보세요.
                            </p>
                        </div>
                    </div>

                    {/* 맨 위에서의 필터 버튼 — 하얀 바 위의 파란 버튼 */}
                    <button
                        ref={topButtonRef}
                        type="button"
                        onClick={() => setOpen(true)}
                        className="lg:hidden absolute left-0 top-1/2 -translate-y-1/2 z-10 flex items-center gap-1.5 px-3 py-1.5 bg-blue-600 text-white hover:bg-blue-700 active:bg-blue-800 rounded-lg text-sm font-bold shadow-sm transition-colors"
                    >
                        <Menu size={16} />
                        필터
                    </button>

                    {/* 공유하기 — PC: 제목 줄 오른쪽 끝의 '공유' 버튼 / 모바일: 오른쪽 위 ⋮ 메뉴(공유하기·홈 화면에 설치) */}
                    <OverflowMenu variant="hero" onShare={share} />
                    <button
                        type="button"
                        onClick={share}
                        aria-label="사이트 공유하기"
                        className="hidden lg:flex absolute right-0 top-1/2 -translate-y-1/2 z-10 items-center gap-1.5 px-3 py-1.5 bg-white text-gray-700 border border-gray-300 hover:bg-gray-50 active:bg-gray-100 rounded-lg text-sm font-bold transition-colors"
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
                        <OverflowMenu variant="bar" onShare={share} />
                    </div>
                </div>
            )}

            <ShareToast message={toast} />
        </>
    );
}
