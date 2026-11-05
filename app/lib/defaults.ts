// 처음 접속했을 때의 기본 보기. 사용자는 자유롭게 바꿀 수 있고, "필터 초기화"를 누르면 이 상태로 돌아온다.
export type SortKey = 'newest' | 'deadline' | 'popular';

export const DEFAULT_SORT: SortKey = 'popular';   // 인기순(신청자 많은 순)

export interface Filters {
    platforms: string[];
    province: string;
    cities: string[];
    categories: string[];
    channels: string[];
    minReward: number;
    hideClosed: boolean;
}

/** 기본 필터: 카테고리 '음식점', 마감된 캠페인 숨기기 켜짐. (배열이 공유되지 않도록 매번 새로 만든다) */
export function createDefaultFilters(): Filters {
    return {
        platforms: [],
        province: '',
        cities: [],
        categories: ['음식점'],
        channels: [],
        minReward: 0,
        hideClosed: true,
    };
}
