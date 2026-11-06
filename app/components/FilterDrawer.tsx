'use client';

import { createContext, useContext, useState, ReactNode } from 'react';

// 모바일 필터 서랍(사이드바)의 열림/닫힘 상태를 제목 줄의 '필터' 버튼과 목록 화면이 함께 쓰도록 공유한다.
interface FilterDrawerValue {
    open: boolean;
    setOpen: (value: boolean) => void;
}

const FilterDrawerContext = createContext<FilterDrawerValue | null>(null);

export function FilterDrawerProvider({ children }: { children: ReactNode }) {
    const [open, setOpen] = useState(false);
    return <FilterDrawerContext.Provider value={{ open, setOpen }}>{children}</FilterDrawerContext.Provider>;
}

export function useFilterDrawer(): FilterDrawerValue {
    const ctx = useContext(FilterDrawerContext);
    if (!ctx) throw new Error('useFilterDrawer는 FilterDrawerProvider 안에서만 사용할 수 있습니다');
    return ctx;
}
