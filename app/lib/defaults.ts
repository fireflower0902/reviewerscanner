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

/** 기본 필터: 카테고리 '음식점', 채널 '네이버 블로그', 마감된 캠페인 숨기기 켜짐. (배열이 공유되지 않도록 매번 새로 만든다) */
export function createDefaultFilters(): Filters {
    return {
        platforms: [],
        province: '',
        cities: [],
        categories: ['음식점'],
        channels: ['네이버 블로그'],
        minReward: 0,
        hideClosed: true,
    };
}

/** 비슷한 카테고리는 하나로 합쳐서 보여준다 (표시·필터 모두 합쳐진 이름 사용). 크롤러 원본 데이터는 그대로 둔다. */
export const CATEGORY_ALIAS: Record<string, string> = {
    '배달': '음식점',
    '포장': '음식점',
    '식품': '음식점',
    '여행': '여행/숙박',
    '숙박': '여행/숙박',
    '문화': '문화/레저',
    '레저': '문화/레저',
};
export const normalizeCategory = (category: string): string => CATEGORY_ALIAS[category] ?? category;
