'use client';

import { useEffect, useRef, useState } from 'react';
import { AD_CONFIG } from '../lib/adConfig';

declare global {
    interface Window {
        PartnersCoupang?: { G: new (options: Record<string, unknown>) => unknown };
    }
}

const COUPANG_SCRIPT = 'https://ads-partners.coupang.com/g.js';

/**
 * 화면 맨 아래에 고정되는 광고 띠.
 *  - 광고 종류는 app/lib/adConfig.ts 의 provider 로 바꾼다.
 *  - 쿠팡일 때는 광고 바로 아래에 공정위 문구를 작게 함께 표시한다.
 *  - PC·모바일 모두 표시한다. 배너 가로 크기는 설정값(680)을 상한으로 화면 너비에 맞춘다.
 */
export default function AdBar() {
    const { provider, coupang, disclosure } = AD_CONFIG;
    const slotRef = useRef<HTMLDivElement>(null);
    const barRef = useRef<HTMLDivElement>(null);
    const [failed, setFailed] = useState(false);
    const [barHeight, setBarHeight] = useState(0);
    const [bannerWidth, setBannerWidth] = useState(0);   // 0 = 아직 화면 너비를 모름(광고 로드 전)

    // 화면 너비에 맞는 배너 너비 계산 (설정값 680을 넘지 않게, 좌우 여백 16px). 화면 크기가 크게 바뀌면(회전 등) 다시 계산한다
    useEffect(() => {
        if (provider !== 'coupang') return;
        const max = Number(coupang.width);
        const calc = () => Math.max(260, Math.min(max, window.innerWidth - 16));
        setBannerWidth(calc());
        let timer: ReturnType<typeof setTimeout>;
        const onResize = () => {
            clearTimeout(timer);
            timer = setTimeout(() => {
                const next = calc();
                setBannerWidth((prev) => (Math.abs(prev - next) > 24 ? next : prev));
            }, 300);
        };
        window.addEventListener('resize', onResize);
        return () => {
            clearTimeout(timer);
            window.removeEventListener('resize', onResize);
        };
    }, [provider, coupang.width]);

    // 쿠팡 광고 불러오기: g.js를 한 번 로드하고, 우리 칸(container) 안에 광고를 그리게 한다
    useEffect(() => {
        if (provider !== 'coupang' || bannerWidth === 0) return;
        const slot = slotRef.current;
        if (!slot) return;
        slot.innerHTML = '';   // 재실행(너비 변경) 시 중복 방지

        const render = () => {
            try {
                new window.PartnersCoupang!.G({ ...coupang, width: String(bannerWidth), container: slot });
            } catch (e) {
                console.warn('쿠팡 광고 표시 실패', e);
                setFailed(true);
            }
        };

        if (window.PartnersCoupang) {
            render();
            return;
        }
        let script = document.querySelector<HTMLScriptElement>(`script[src="${COUPANG_SCRIPT}"]`);
        if (!script) {
            script = document.createElement('script');
            script.src = COUPANG_SCRIPT;
            script.async = true;
            document.body.appendChild(script);
        }
        script.addEventListener('load', render);
        script.addEventListener('error', () => setFailed(true));   // 광고 차단 프로그램 등으로 막히면 띠를 숨긴다
        return () => script?.removeEventListener('load', render);
    }, [provider, coupang, bannerWidth]);

    // 띠 높이를 재서 (1) 마지막 카드가 가려지지 않게 아래 여백을 확보하고 (2) 사이드바 높이를 맞춘다
    useEffect(() => {
        const bar = barRef.current;
        if (!bar) return;
        const update = () => {
            const h = bar.offsetHeight;
            setBarHeight(h);
            document.documentElement.style.setProperty('--ad-bar-h', `${h}px`);
        };
        update();
        const ro = new ResizeObserver(update);
        ro.observe(bar);
        return () => {
            ro.disconnect();
            document.documentElement.style.removeProperty('--ad-bar-h');
        };
    }, [provider, failed]);

    // 'adsense'는 아직 연결 코드가 없어 표시하지 않는다(승인 후 이 자리에 <ins class="adsbygoogle"> 추가)
    if (provider !== 'coupang' || failed) return null;

    return (
        <>
            {/* 고정된 띠가 마지막 카드를 가리지 않도록 같은 높이의 빈 공간 */}
            <div aria-hidden="true" style={{ height: barHeight }} />
            <div
                ref={barRef}
                className="fixed bottom-0 left-0 right-0 z-30 bg-white border-t border-gray-200 shadow-[0_-2px_8px_rgba(0,0,0,0.06)]"
                style={{ paddingBottom: 'env(safe-area-inset-bottom)' }}
            >
                <div className="mx-auto flex flex-col items-center px-2 md:px-4 pt-1.5 pb-1">
                    <div
                        ref={slotRef}
                        style={{ width: bannerWidth || Number(coupang.width), maxWidth: '100%', minHeight: Number(coupang.height) }}
                    />
                    <p className="mt-0.5 text-center text-[10.5px] sm:text-[11px] leading-tight text-gray-600">{disclosure}</p>
                </div>
            </div>
        </>
    );
}
