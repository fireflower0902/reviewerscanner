'use client';

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { Download, Share, X, MoreVertical, PlusSquare } from 'lucide-react';

type Env = 'android' | 'ios' | 'desktop';

interface InstallPromptEvent extends Event {
    prompt: () => Promise<void>;
    userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }>;
}

interface InstallGuideContextValue {
    /** 설치 안내 창 열기 */
    openGuide: () => void;
    /** '설치' 누르기: 브라우저가 설치 창을 바로 띄워 줄 수 있으면(안드로이드 크롬 등) 그 창을, 아니면(아이폰 등) 안내 창을 연다 */
    requestInstall: () => void;
    /** 이미 앱(홈 화면)으로 열려 있으면 true — 설치 메뉴를 숨긴다 */
    installed: boolean;
}

const InstallGuideContext = createContext<InstallGuideContextValue>({ openGuide: () => {}, requestInstall: () => {}, installed: true });

export const useInstallGuide = () => useContext(InstallGuideContext);

/**
 * "앱처럼 설치하기" 안내 (PWA).
 *  - 이미 설치해서 앱으로 열었으면 아무것도 보이지 않는다.
 *  - 안드로이드 크롬 등 설치 창을 바로 띄울 수 있으면 [설치하기] 버튼을 보여주고, 아니면 단계별 안내를 보여준다.
 *  - 아이폰은 브라우저가 설치 창을 지원하지 않아 사파리의 '홈 화면에 추가' 방법을 안내한다.
 *  - 카카오톡 안의 브라우저에서는 설치가 안 되므로 먼저 '다른 브라우저로 열기'를 안내한다.
 */
export default function InstallGuideProvider({ children }: { children: React.ReactNode }) {
    const [installed, setInstalled] = useState(true);       // 첫 렌더에서는 숨김 (서버 렌더와 맞추기)
    const [open, setOpen] = useState(false);
    const [env, setEnv] = useState<Env>('desktop');
    const [tab, setTab] = useState<Env>('android');
    const [inKakao, setInKakao] = useState(false);
    const [prompt, setPrompt] = useState<InstallPromptEvent | null>(null);

    useEffect(() => {
        const standalone =
            window.matchMedia('(display-mode: standalone)').matches ||
            (navigator as Navigator & { standalone?: boolean }).standalone === true;
        setInstalled(standalone);

        const ua = navigator.userAgent;
        const ios = /iPhone|iPad|iPod/i.test(ua) || (/Macintosh/i.test(ua) && navigator.maxTouchPoints > 1);
        const android = /Android/i.test(ua);
        const detected: Env = ios ? 'ios' : android ? 'android' : 'desktop';
        setEnv(detected);
        setTab(detected === 'desktop' ? 'android' : detected);
        setInKakao(/KAKAOTALK/i.test(ua));

        const onPrompt = (e: Event) => { e.preventDefault(); setPrompt(e as InstallPromptEvent); };
        const onInstalled = () => { setInstalled(true); setOpen(false); };
        window.addEventListener('beforeinstallprompt', onPrompt);
        window.addEventListener('appinstalled', onInstalled);
        return () => {
            window.removeEventListener('beforeinstallprompt', onPrompt);
            window.removeEventListener('appinstalled', onInstalled);
        };
    }, []);

    useEffect(() => {
        if (!open) return;
        const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') setOpen(false); };
        window.addEventListener('keydown', onKey);
        return () => window.removeEventListener('keydown', onKey);
    }, [open]);

    const openGuide = useCallback(() => setOpen(true), []);

    // 브라우저의 설치 창 띄우기 (한 번만 쓸 수 있어서, 쓰고 나면 비운다)
    const install = useCallback(async () => {
        if (!prompt) return;
        const current = prompt;
        setPrompt(null);
        try {
            await current.prompt();
            const choice = await current.userChoice;
            if (choice.outcome === 'accepted') setOpen(false);
        } catch {
            setOpen(true);   // 설치 창을 못 띄우면 안내 창으로
        }
    }, [prompt]);

    const requestInstall = useCallback(() => {
        if (prompt) void install();
        else setOpen(true);
    }, [prompt, install]);

    const value = useMemo(() => ({ openGuide, requestInstall, installed }), [openGuide, requestInstall, installed]);

    return (
        <InstallGuideContext.Provider value={value}>
            {children}

            {open && !installed && (
                <div
                    className="fixed inset-0 z-[70] flex items-end justify-center bg-black/50 sm:items-center"
                    role="dialog"
                    aria-modal="true"
                    aria-label="앱처럼 설치하기"
                    onClick={() => setOpen(false)}
                >
                    <div
                        className="max-h-[90vh] w-full max-w-md overflow-y-auto rounded-t-2xl bg-white p-5 shadow-2xl sm:rounded-2xl"
                        onClick={(e) => e.stopPropagation()}
                    >
                        <div className="flex items-start justify-between gap-3">
                            <div>
                                <h2 className="text-lg font-bold text-gray-900">체험단 스캐너를 앱처럼 설치하기</h2>
                                <p className="mt-1 text-sm text-gray-600">
                                    홈 화면에 아이콘이 생기고, 주소창 없이 앱처럼 열려요. 무료이고 스토어는 필요 없어요.
                                </p>
                            </div>
                            <button
                                type="button"
                                onClick={() => setOpen(false)}
                                aria-label="닫기"
                                className="rounded-full p-1.5 text-gray-400 hover:bg-gray-100 hover:text-gray-700"
                            >
                                <X size={18} />
                            </button>
                        </div>

                        {inKakao && (
                            <div className="mt-4 rounded-xl border border-amber-200 bg-amber-50 p-3 text-sm text-amber-900">
                                <b>카카오톡 안에서는 설치할 수 없어요.</b>
                                <br />
                                화면 오른쪽 아래 <b>⋯</b> 메뉴 → <b>다른 브라우저로 열기</b>를 누른 뒤, 아래 방법으로 설치해 주세요.
                            </div>
                        )}

                        <div className="mt-4 grid grid-cols-2 gap-1 rounded-lg bg-gray-100 p-1 text-sm font-semibold">
                            {(['android', 'ios'] as const).map((t) => (
                                <button
                                    key={t}
                                    type="button"
                                    onClick={() => setTab(t)}
                                    className={`rounded-md py-1.5 transition-colors ${tab === t ? 'bg-white text-blue-700 shadow-sm' : 'text-gray-500'}`}
                                >
                                    {t === 'android' ? '안드로이드' : '아이폰'}
                                </button>
                            ))}
                        </div>

                        {tab === 'android' ? (
                            <div className="mt-4 space-y-3 text-sm text-gray-800">
                                {prompt && env !== 'ios' && (
                                    <button
                                        type="button"
                                        onClick={install}
                                        className="flex w-full items-center justify-center gap-2 rounded-xl bg-blue-600 py-3 text-base font-bold text-white hover:bg-blue-700"
                                    >
                                        <Download size={18} /> 지금 설치하기
                                    </button>
                                )}
                                <Step n={1}>크롬으로 이 사이트를 열어요.</Step>
                                <Step n={2}>
                                    오른쪽 위 <MoreVertical size={14} className="inline align-text-bottom" /> 메뉴를 눌러요.
                                </Step>
                                <Step n={3}><b>앱 설치</b> 또는 <b>홈 화면에 추가</b>를 눌러요.</Step>
                                <Step n={4}>홈 화면에 생긴 <b>체험단 스캐너</b> 아이콘으로 열면 끝!</Step>
                            </div>
                        ) : (
                            <div className="mt-4 space-y-3 text-sm text-gray-800">
                                <Step n={1}><b>사파리</b>로 이 사이트를 열어요. (카카오톡 안에서는 안 돼요)</Step>
                                <Step n={2}>
                                    화면 아래 <Share size={14} className="inline align-text-bottom" /> <b>공유</b> 버튼을 눌러요.
                                </Step>
                                <Step n={3}>
                                    <PlusSquare size={14} className="inline align-text-bottom" /> <b>홈 화면에 추가</b>를 누르고, 오른쪽 위 <b>추가</b>를 눌러요.
                                </Step>
                                <Step n={4}>홈 화면에 생긴 <b>체험단 스캐너</b> 아이콘으로 열면 끝!</Step>
                            </div>
                        )}

                        <p className="mt-4 text-xs text-gray-400">
                            사이트가 바뀌면 설치한 앱도 자동으로 최신이 돼요. 지우고 싶으면 아이콘을 길게 눌러 삭제하면 돼요.
                        </p>
                    </div>
                </div>
            )}
        </InstallGuideContext.Provider>
    );
}

function Step({ n, children }: { n: number; children: React.ReactNode }) {
    return (
        <div className="flex items-start gap-3">
            <span className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-blue-100 text-xs font-bold text-blue-700">
                {n}
            </span>
            <p className="leading-6">{children}</p>
        </div>
    );
}
