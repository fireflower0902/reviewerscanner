'use client';

import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react';
import { X } from 'lucide-react';
import GuideContent, { GUIDE_SUBTITLE } from './content/GuideContent';
import TermsContent, { TERMS_UPDATED } from './content/TermsContent';

type Kind = 'guide' | 'terms';

interface InfoModalContextValue {
    /** 이용가이드 / 이용약관 팝업 창 열기 */
    open: (kind: Kind) => void;
}

const InfoModalContext = createContext<InfoModalContextValue>({ open: () => {} });
export const useInfoModal = () => useContext(InfoModalContext);

const TITLES: Record<Kind, string> = { guide: '이용가이드', terms: '이용약관' };

/**
 * 홈 화면 위에 이용가이드·이용약관을 팝업 창으로 띄운다.
 *  - 닫으면 (X, 아래 닫기 버튼, 바깥 클릭, Esc, 폰의 '뒤로 가기') 하던 화면(선택한 필터 포함) 그대로 돌아온다.
 *  - 주소 끝에 #guide / #terms 를 잠깐 붙여서, 폰의 뒤로 가기 버튼으로도 팝업이 닫히게 한다.
 */
export function InfoModalProvider({ children }: { children: React.ReactNode }) {
    const [kind, setKind] = useState<Kind | null>(null);
    const pushed = useRef(false);            // 팝업을 위해 기록(history)을 한 칸 추가했는가
    const scrollRef = useRef<HTMLDivElement>(null);
    const closeBtnRef = useRef<HTMLButtonElement>(null);

    const open = useCallback((k: Kind) => {
        setKind(k);
        if (pushed.current) {
            window.history.replaceState({ infoModal: true }, '', `#${k}`);
        } else {
            window.history.pushState({ infoModal: true }, '', `#${k}`);
            pushed.current = true;
        }
    }, []);

    const close = useCallback(() => {
        if (pushed.current) {
            pushed.current = false;
            window.history.back();           // popstate 에서 팝업을 닫는다 (주소의 # 도 함께 사라짐)
        } else {
            setKind(null);
        }
    }, []);

    useEffect(() => {
        const onPop = () => { pushed.current = false; setKind(null); };
        window.addEventListener('popstate', onPop);
        return () => window.removeEventListener('popstate', onPop);
    }, []);

    // 열려 있는 동안: 뒤 화면 스크롤 잠금, Esc 로 닫기, 닫기 버튼에 포커스
    useEffect(() => {
        if (!kind) return;
        const prev = document.body.style.overflow;
        document.body.style.overflow = 'hidden';
        const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') close(); };
        window.addEventListener('keydown', onKey);
        closeBtnRef.current?.focus();
        return () => {
            document.body.style.overflow = prev;
            window.removeEventListener('keydown', onKey);
        };
    }, [kind, close]);

    // 탭을 바꾸면 본문을 맨 위로
    useEffect(() => { scrollRef.current?.scrollTo({ top: 0 }); }, [kind]);

    const value = useMemo(() => ({ open }), [open]);

    return (
        <InfoModalContext.Provider value={value}>
            {children}
            {kind && (
                <div
                    className="fixed inset-0 z-[80] flex items-end justify-center bg-black/55 sm:items-center sm:p-6"
                    onClick={close}
                    role="dialog"
                    aria-modal="true"
                    aria-label={TITLES[kind]}
                >
                    <div
                        className="flex h-[92vh] w-full max-w-3xl flex-col overflow-hidden rounded-t-2xl bg-white shadow-2xl sm:h-[85vh] sm:rounded-2xl"
                        onClick={(e) => e.stopPropagation()}
                    >
                        {/* 위쪽: 탭 + 닫기 */}
                        <div className="flex items-center justify-between gap-3 border-b border-gray-200 bg-white px-4 py-3">
                            <div className="flex gap-1 rounded-lg bg-gray-100 p-1 text-sm font-semibold">
                                {(['guide', 'terms'] as const).map((k) => (
                                    <button
                                        key={k}
                                        type="button"
                                        onClick={() => open(k)}
                                        className={`rounded-md px-3 py-1.5 transition-colors ${kind === k ? 'bg-white text-blue-700 shadow-sm' : 'text-gray-500 hover:text-gray-800'}`}
                                    >
                                        {TITLES[k]}
                                    </button>
                                ))}
                            </div>
                            <button
                                ref={closeBtnRef}
                                type="button"
                                onClick={close}
                                aria-label="닫기"
                                className="flex items-center gap-1 rounded-lg border border-gray-300 px-3 py-1.5 text-sm font-bold text-gray-700 hover:bg-gray-50 active:bg-gray-100"
                            >
                                <X size={16} />
                                닫기
                            </button>
                        </div>

                        {/* 본문 */}
                        <div ref={scrollRef} className="flex-1 overflow-y-auto px-5 py-6 sm:px-8">
                            <h2 className="text-2xl font-extrabold tracking-tight">{TITLES[kind]}</h2>
                            <p className="mt-1 text-sm text-gray-500">{kind === 'guide' ? GUIDE_SUBTITLE : TERMS_UPDATED}</p>
                            <div className="mt-6 space-y-10 text-[15px] leading-7 text-gray-800">
                                {kind === 'guide' ? <GuideContent /> : <TermsContent />}
                            </div>
                        </div>

                        {/* 아래쪽: 눈에 띄는 닫기 */}
                        <div className="border-t border-gray-200 bg-white px-4 py-3">
                            <button
                                type="button"
                                onClick={close}
                                className="w-full rounded-xl bg-blue-600 py-3 text-base font-bold text-white shadow-sm hover:bg-blue-700 active:bg-blue-800"
                            >
                                닫고 체험단 계속 찾아보기
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </InfoModalContext.Provider>
    );
}
