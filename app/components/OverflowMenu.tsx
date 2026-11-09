'use client';

import { useEffect, useRef, useState } from 'react';
import { MoreVertical, Share2, Download, BookOpen, FileText } from 'lucide-react';
import { useInstallGuide } from './InstallGuide';
import { useInfoModal } from './InfoModal';

/**
 * 모바일 오른쪽 위 점 세 개(⋮) 메뉴: [공유하기] [홈 화면에 설치]
 *  - variant 'hero' : 파란 제목 줄 위 (반투명 유리 버튼)
 *  - variant 'bar'  : 스크롤 후 하얀 고정 띠 안 (테두리 버튼)
 */
export default function OverflowMenu({
    variant,
    onShare,
}: {
    variant: 'hero' | 'bar';
    onShare: () => void;
}) {
    const [open, setOpen] = useState(false);
    const wrapRef = useRef<HTMLDivElement>(null);
    const { requestInstall, installed } = useInstallGuide();
    const { open: openInfo } = useInfoModal();

    // 바깥을 누르거나 Esc 를 누르면 닫기
    useEffect(() => {
        if (!open) return;
        const onDown = (e: PointerEvent) => {
            if (wrapRef.current && !wrapRef.current.contains(e.target as Node)) setOpen(false);
        };
        const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') setOpen(false); };
        document.addEventListener('pointerdown', onDown);
        document.addEventListener('keydown', onKey);
        return () => {
            document.removeEventListener('pointerdown', onDown);
            document.removeEventListener('keydown', onKey);
        };
    }, [open]);

    const buttonClass =
        'border border-gray-300 text-gray-700 hover:bg-gray-50 active:bg-gray-100';

    const run = (fn: () => void) => () => { setOpen(false); fn(); };

    return (
        <div ref={wrapRef} className={variant === 'hero' ? 'lg:hidden absolute right-0 top-1/2 -translate-y-1/2 z-20' : 'lg:hidden relative'}>
            <button
                type="button"
                onClick={() => setOpen((v) => !v)}
                aria-label="더보기 메뉴"
                aria-haspopup="menu"
                aria-expanded={open}
                className={`flex h-[34px] w-[34px] items-center justify-center rounded-lg transition-colors ${buttonClass}`}
            >
                <MoreVertical size={18} />
            </button>

            {open && (
                <div
                    role="menu"
                    className="absolute right-0 top-full z-50 mt-1.5 w-52 overflow-hidden rounded-xl border border-gray-200 bg-white py-1 text-gray-800 shadow-xl"
                >
                    <button
                        type="button"
                        role="menuitem"
                        onClick={run(onShare)}
                        className="flex w-full items-center gap-2.5 px-4 py-3 text-left text-sm font-medium hover:bg-gray-50 active:bg-gray-100"
                    >
                        <Share2 size={16} className="text-blue-600" />
                        공유하기
                    </button>
                    {!installed && (
                        <button
                            type="button"
                            role="menuitem"
                            onClick={run(requestInstall)}
                            className="flex w-full items-center gap-2.5 border-t border-gray-100 px-4 py-3 text-left text-sm font-medium hover:bg-gray-50 active:bg-gray-100"
                        >
                            <Download size={16} className="text-blue-600" />
                            홈 화면에 설치
                        </button>
                    )}
                    <button
                        type="button"
                        role="menuitem"
                        onClick={run(() => openInfo('guide'))}
                        className="flex w-full items-center gap-2.5 border-t border-gray-100 px-4 py-3 text-left text-sm font-medium hover:bg-gray-50 active:bg-gray-100"
                    >
                        <BookOpen size={16} className="text-blue-600" />
                        이용가이드
                    </button>
                    <button
                        type="button"
                        role="menuitem"
                        onClick={run(() => openInfo('terms'))}
                        className="flex w-full items-center gap-2.5 border-t border-gray-100 px-4 py-3 text-left text-sm font-medium hover:bg-gray-50 active:bg-gray-100"
                    >
                        <FileText size={16} className="text-blue-600" />
                        이용약관
                    </button>
                </div>
            )}
        </div>
    );
}
