'use client';

import { useState, useMemo, useEffect } from 'react';
import { Campaign } from '../types/campaign';
import { kstDaysPassed, shiftDday, normalizeDday, readJsonMaybeGzip } from '../lib/dday';
import { createDefaultFilters, DEFAULT_SORT, SortKey, Filters } from '../lib/defaults';
import CampaignCard from './CampaignCard';
import SidebarFilter from './SidebarFilter';
import { Search, Filter } from 'lucide-react';
import { useFilterDrawer } from './FilterDrawer';

// 데이터 파일 주소: 운영은 Cloudflare Pages Function(/api/campaigns, R2에서 읽음),
// 로컬 개발은 크롤러가 만든 public/campaigns.json
const DATA_URL = process.env.NODE_ENV === 'development' ? '/campaigns.json' : '/api/campaigns';

export default function CampaignList() {
    const [campaigns, setCampaigns] = useState<Campaign[]>([]);
    const [loadState, setLoadState] = useState<'loading' | 'ready' | 'error'>('loading');
    const [reloadKey, setReloadKey] = useState(0);

    useEffect(() => {
        const controller = new AbortController();
        setLoadState('loading');
        fetch(DATA_URL, { signal: controller.signal })
            .then(async (res) => {
                if (!res.ok) throw new Error(`HTTP ${res.status}`);
                return { data: await readJsonMaybeGzip<Campaign[]>(res), generatedAt: res.headers.get('x-generated-at') };
            })
            .then(({ data, generatedAt }) => {
                // 마감 표기 통일("오늘까지"/"0일 남음" -> "오늘마감") — 크롤러 데이터가 갱신되기 전에도 적용
                const list = (Array.isArray(data) ? data : []).map((c) => {
                    const dday = normalizeDday(c.meta.dday);
                    return dday === c.meta.dday ? c : { ...c, meta: { ...c.meta, dday } };
                });
                // 수집 이후 날짜가 바뀐 만큼 마감 표기를 보정 (헤더가 없으면 보정 없음)
                const daysPassed = generatedAt ? kstDaysPassed(generatedAt) : 0;
                const adjusted = daysPassed > 0
                    ? list.flatMap((c) => {
                        const dday = shiftDday(c.meta.dday, daysPassed);
                        return dday === null ? [] : [{ ...c, meta: { ...c.meta, dday } }];
                    })
                    : list;
                setCampaigns(adjusted);
                setLoadState('ready');
            })
            .catch((err) => {
                if (err.name === 'AbortError') return;
                console.error('Failed to load campaigns:', err);
                setLoadState('error');
            });
        return () => controller.abort();
    }, [reloadKey]);

    const [keyword, setKeyword] = useState('');
    const { open: isSidebarOpen, setOpen: setIsSidebarOpen } = useFilterDrawer();   // 모바일 필터 서랍 (제목 줄의 '필터' 버튼과 공유)
    const [isScrolled, setIsScrolled] = useState(false);

    // Complex Filter State
    const [filters, setFilters] = useState<Filters>(createDefaultFilters);   // 기본: 음식점 + 마감 숨기기

    // Infinite Scroll State
    const [visibleCount, setVisibleCount] = useState(40);
    const ITEMS_PER_PAGE = 40;

    // Sort State
    const [sortBy, setSortBy] = useState<SortKey>(DEFAULT_SORT)   // 기본: 인기순;

    // Reset visible count when filters or sort change
    useEffect(() => {
        setVisibleCount(ITEMS_PER_PAGE);
    }, [keyword, filters, sortBy]);

    // 모바일 스크롤 감지: 조금이라도 내리면 isScrolled = true
    useEffect(() => {
        const handleScroll = () => {
            setIsScrolled(window.scrollY > 10);
        };
        handleScroll();
        window.addEventListener('scroll', handleScroll, { passive: true });
        return () => window.removeEventListener('scroll', handleScroll);
    }, []);

    // Platform initialization removed; default [] means 'All'


    // 검색어를 쉼표로 나눠 공백을 정리한 단어 목록으로 만든다 ("화성시, 고기" -> ["화성시", "고기"])
    const keywordTerms = useMemo(
        () => keyword.split(',').map((t) => t.trim().toLowerCase()).filter(Boolean),
        [keyword]
    );

    const filtered = useMemo(() => {
        return campaigns.filter(c => {
            // 1. Keyword — 쉼표(,)로 구분한 모든 단어를 포함해야 통과(AND). 단어마다 제목/보상/지역/카테고리 중 어디든 있으면 됨
            const matchesKeyword = keywordTerms.length === 0 || (() => {
                const haystack = `${c.title} ${c.reward.text} ${c.region.normalized} ${c.category}`.toLowerCase();
                return keywordTerms.every((term) => haystack.includes(term));
            })();

            // 2. Platform
            const matchesPlatform = filters.platforms.length === 0 || filters.platforms.includes(c.platform);

            // 3. Region
            let matchesRegion = true;
            if (filters.province) {
                matchesRegion = c.region.province === filters.province;
                // Multi-city logic
                if (matchesRegion && filters.cities.length > 0) {
                    matchesRegion = filters.cities.includes(c.region.city);
                }
            }

            // 4. Channel (Exact Match for 6 types)
            let matchesChannel = true;
            if (filters.channels.length > 0) {
                matchesChannel = filters.channels.includes(c.meta.type);
            }

            // 5. Category
            let matchesCategory = true;
            if (filters.categories && filters.categories.length > 0) {
                matchesCategory = filters.categories.includes(c.category);
            }

            // 6. Min Reward
            let matchesReward = true;
            if (filters.minReward > 0) {
                matchesReward = c.reward.value >= filters.minReward;
            }

            // 6. Hide Closed / Deadline logic
            let matchesOpen = true;
            if (filters.hideClosed) {
                // Parse D-Day: "11일 남음", "오늘 선정 마감", "마감"
                const ddayStr = c.meta.dday;
                if (ddayStr.includes("마감") && !ddayStr.includes("오늘")) {
                    matchesOpen = false;
                }
            }

            return matchesKeyword && matchesPlatform && matchesRegion && matchesCategory && matchesChannel && matchesReward && matchesOpen;
        });
    }, [campaigns, keywordTerms, filters]);

    // Sorting logic
    const parseDDay = (ddayStr: string): number => {
        if (!ddayStr) return -1;
        if (ddayStr.includes("마감") && !ddayStr.includes("오늘")) return -1;
        if (ddayStr.includes("오늘")) return 0;
        const match = ddayStr.match(/(\d+)일/);
        if (match) return parseInt(match[1], 10);
        return -1; // Fallback
    };

    const sorted = useMemo(() => {
        return [...filtered].sort((a, b) => {
            if (sortBy === 'popular') {
                return (b.stats?.applicants || 0) - (a.stats?.applicants || 0);
            }

            const aDDay = parseDDay(a.meta.dday);
            const bDDay = parseDDay(b.meta.dday);

            if (sortBy === 'newest') {
                // 아직 일정이 많이 남은 것부터 (Larger D-Day first)
                return bDDay - aDDay;
            } else if (sortBy === 'deadline') {
                // 마감임박순: 신청 일정이 많이 남지 않은 것 부터 (Smaller positive D-Day first)
                // -1 (마감)은 가장 뒤로 보냄
                if (aDDay === -1 && bDDay === -1) return 0;
                if (aDDay === -1) return 1;
                if (bDDay === -1) return -1;
                return aDDay - bDDay;
            }
            return 0;
        });
    }, [filtered, sortBy]);

    // Derived visible items using the sorted array
    const visibleCampaigns = useMemo(() => {
        return sorted.slice(0, visibleCount);
    }, [sorted, visibleCount]);

    // Intersection Observer for Infinite Scroll

    useEffect(() => {
        const observer = new IntersectionObserver(
            (entries) => {
                if (entries[0].isIntersecting) {
                    setVisibleCount((prev) => Math.min(prev + ITEMS_PER_PAGE, filtered.length));
                }
            },
            { threshold: 0.1, rootMargin: '100px' }
        );

        const sentinel = document.getElementById('scroll-sentinel');
        if (sentinel) observer.observe(sentinel);

        return () => observer.disconnect();
    }, [filtered.length, visibleCount]);

    return (
        <div className="flex min-h-screen bg-gray-50">
            {/* Sidebar */}
            <SidebarFilter
                campaigns={campaigns}
                filters={filters}
                onFilterChange={setFilters}
                isOpen={isSidebarOpen}
                onClose={() => setIsSidebarOpen(false)}
            />

            {/* Main Content */}
            <div id="main-scroll-container" className="flex-1 flex flex-col min-w-0">
                <div className="p-4 pt-2 sm:p-6 lg:p-8 lg:pt-4">
                    {/* Search Bar */}
                    <div className="max-w-4xl mx-auto mb-4 sm:mb-8 lg:mb-4">
                        <div className="relative">
                            <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                                <Search className="h-5 w-5 text-gray-400" />
                            </div>
                            <input
                                type="text"
                                className="block w-full pl-11 pr-4 py-3 border border-gray-300 rounded-xl leading-5 bg-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent shadow-sm transition duration-150 ease-in-out"
                                placeholder="캠페인 검색 (키워드, 보상 등) · 쉼표(,)로 여러 단어 입력"
                                value={keyword}
                                onChange={(e) => setKeyword(e.target.value)}
                            />
                        </div>
                        <p className="mt-2 px-1 text-xs text-gray-500">
                            💡 쉼표(,)로 구분하면 <b>모든 단어를 포함</b>한 캠페인만 보여줘요. 예) <span className="font-medium text-gray-700">화성시, 고기</span> (제목·보상·지역·카테고리에서 찾아요)
                        </p>
                    </div>

                    {/* Results Count & Active Filters Summary */}
                    <div className="flex flex-col sm:flex-row justify-between items-start sm:items-end mb-3 gap-2 sm:mb-6 sm:gap-4">
                        <div>
                            <h2 className="text-2xl font-bold text-gray-900">캠페인 리스트</h2>
                            <p className="text-sm text-gray-500 mt-1">
                                {filters.province ? `${filters.province} ` : '전체 지역'}
                                {filters.cities.length > 0 && `> ${filters.cities.join(', ')}`}
                                {' · '}
                                {filters.platforms.length > 0 ? `${filters.platforms.length}개 플랫폼` : '전체 플랫폼'}
                                {filters.minReward > 0 && ` · ${filters.minReward.toLocaleString()}원+`}
                            </p>
                        </div>
                        <div className="flex flex-wrap items-center gap-3">
                            <select
                                value={sortBy}
                                onChange={(e) => setSortBy(e.target.value as any)}
                                className="bg-white border border-gray-200 text-gray-700 text-sm font-medium rounded-lg focus:ring-blue-500 focus:border-blue-500 px-3 py-1.5 shadow-sm outline-none cursor-pointer"
                            >
                                <option value="newest">최신순 (여유순)</option>
                                <option value="deadline">마감임박순</option>
                                <option value="popular">인기순 (신청자 많은순)</option>
                            </select>
                            {loadState === 'ready' && (
                                <div className="text-sm font-medium text-blue-600 bg-blue-50 px-3 py-1.5 rounded-full shrink-0">
                                    총 {filtered.length}개 중 {visibleCampaigns.length}개 표시
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Grid */}
                    {loadState === 'loading' ? (
                        <div className="text-center py-32 bg-white rounded-3xl border border-gray-100 shadow-sm">
                            <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-600 mx-auto mb-4"></div>
                            <p className="text-gray-500">캠페인을 불러오는 중입니다...</p>
                        </div>
                    ) : loadState === 'error' ? (
                        <div className="text-center py-32 bg-white rounded-3xl border border-gray-100 shadow-sm">
                            <h3 className="text-lg font-medium text-gray-900">데이터를 불러오지 못했습니다</h3>
                            <p className="text-gray-500 mt-2">잠시 후 다시 시도해주세요.</p>
                            <button
                                onClick={() => setReloadKey((k) => k + 1)}
                                className="mt-6 px-5 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors"
                            >
                                다시 시도
                            </button>
                        </div>
                    ) : visibleCampaigns.length > 0 ? (
                        <>
                            <div className="grid grid-cols-2 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3 sm:gap-6">
                                {visibleCampaigns.map((campaign, idx) => (
                                    <CampaignCard key={`${campaign.platform}-${idx}`} campaign={campaign} />
                                ))}
                            </div>

                            {/* Sentinel Element for Infinite Scroll */}
                            {visibleCount < filtered.length && (
                                <div id="scroll-sentinel" className="h-20 flex items-center justify-center mt-8">
                                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                                </div>
                            )}
                        </>
                    ) : (
                        <div className="text-center py-32 bg-white rounded-3xl border border-gray-100 shadow-sm">
                            <div className="bg-gray-50 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                                <Filter className="h-8 w-8 text-gray-400" />
                            </div>
                            <h3 className="text-lg font-medium text-gray-900">검색 결과가 없습니다</h3>
                            <p className="text-gray-500 mt-2">필터를 조정하거나 다른 키워드로 검색해보세요.</p>
                            <button
                                onClick={() => {
                                    setKeyword('');
                                    setFilters(createDefaultFilters());
                                }}
                                className="mt-6 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                            >
                                필터 초기화
                            </button>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
