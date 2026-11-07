'use client';

import { useCallback, useEffect, useRef, useState } from 'react';

const SHARE_DATA = {
    title: '체험단 스캐너',
    text: '블로그 체험단 사이트 모음 — 지역·보상별로 한눈에 찾아보세요.',
};

/**
 * 공유하기 동작
 *  - 휴대폰(터치 기기)에서 기본 공유 창을 쓸 수 있으면 그걸 연다 (카카오톡·문자 등 설치된 앱으로 바로 보냄)
 *  - 그 외(PC 등)에는 사이트 주소를 클립보드에 복사하고 안내 문구를 잠깐 보여준다
 */
export function useShare() {
    const [toast, setToast] = useState<string | null>(null);
    const timer = useRef<ReturnType<typeof setTimeout> | null>(null);

    const showToast = useCallback((message: string) => {
        setToast(message);
        if (timer.current) clearTimeout(timer.current);
        timer.current = setTimeout(() => setToast(null), 2400);
    }, []);

    useEffect(() => () => { if (timer.current) clearTimeout(timer.current); }, []);

    const share = useCallback(async () => {
        const url = `${window.location.origin}/`;
        const isTouch = window.matchMedia('(pointer: coarse)').matches;
        if (isTouch && typeof navigator.share === 'function') {
            try {
                await navigator.share({ ...SHARE_DATA, url });
                return;
            } catch (e) {
                if ((e as Error).name === 'AbortError') return;   // 사용자가 공유 창을 닫음
                // 그 외 실패 시 아래 복사 방식으로
            }
        }
        try {
            await navigator.clipboard.writeText(url);
            showToast('링크를 복사했어요. 붙여넣어서 공유하세요!');
        } catch {
            // 오래된 브라우저/권한 거부 대비
            const ta = document.createElement('textarea');
            ta.value = url;
            ta.style.cssText = 'position:fixed;opacity:0;top:0;left:0';
            document.body.appendChild(ta);
            ta.select();
            let ok = false;
            try { ok = document.execCommand('copy'); } catch { /* ignore */ }
            document.body.removeChild(ta);
            showToast(ok ? '링크를 복사했어요. 붙여넣어서 공유하세요!' : '복사하지 못했어요. 주소창의 주소를 직접 복사해 주세요.');
        }
    }, [showToast]);

    return { share, toast };
}

/** 화면 아래 가운데에 잠깐 뜨는 안내 (광고 띠 위에 표시) */
export function ShareToast({ message }: { message: string | null }) {
    return (
        <div
            aria-live="polite"
            className="pointer-events-none fixed left-0 right-0 z-[60] flex justify-center px-4"
            style={{ bottom: 'calc(var(--ad-bar-h, 0px) + 16px)' }}
        >
            {message && (
                <div className="rounded-full bg-gray-900/90 px-4 py-2.5 text-sm font-medium text-white shadow-lg">
                    {message}
                </div>
            )}
        </div>
    );
}
