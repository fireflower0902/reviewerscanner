'use client';

import { useState, useMemo, useEffect } from 'react';
import { Campaign } from '../types/campaign';
import CampaignCard from './CampaignCard';
import SidebarFilter from './SidebarFilter';
import { Search, Filter, Menu } from 'lucide-react';

interface CampaignListProps {
    initialCampaigns: Campaign[];
}

export default function CampaignList({ initialCampaigns }: CampaignListProps) {
    const [keyword, setKeyword] = useState('');
    const [isSidebarOpen, setIsSidebarOpen] = useState(false);

    // Complex Filter State
    const [filters, setFilters] = useState({
        platforms: [] as string[],
        province: '',
        cities: [] as string[],
        categories: [] as string[], // New
        channels: [] as string[],
        minReward: 0,
        hideClosed: false
    });

    // Infinite Scroll State
    const [visibleCount, setVisibleCount] = useState(40);
    const ITEMS_PER_PAGE = 40;

    // Sort State
    const [sortBy, setSortBy] = useState<'newest' | 'deadline' | 'popular'>('newest');

    // Reset visible count when filters or sort change
    useEffect(() => {
        setVisibleCount(ITEMS_PER_PAGE);
    }, [keyword, filters, sortBy]);

    // Platform initialization removed; default [] means 'All'


    const filtered = useMemo(() => {
        return initialCampaigns.filter(c => {
            // 1. Keyword
            const matchesKeyword = c.title.toLowerCase().includes(keyword.toLowerCase()) ||
                c.reward.text.toLowerCase().includes(keyword.toLowerCase());

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
    }, [initialCampaigns, keyword, filters]);

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
                campaigns={initialCampaigns}
                filters={filters}
                onFilterChange={setFilters}
                isOpen={isSidebarOpen}
                onClose={() => setIsSidebarOpen(false)}
            />

            {/* Main Content */}
            <div className="flex-1 flex flex-col min-w-0 h-screen overflow-y-auto">
                {/* Mobile Header for Sidebar Toggle */}
                <div className="lg:hidden bg-white border-b border-gray-200 p-4 flex items-center justify-between sticky top-0 z-20">
                    <h1 className="text-lg font-bold text-gray-900">리뷰어 스캐너</h1>
                    <button
                        onClick={() => setIsSidebarOpen(true)}
                        className="p-2 text-gray-600 hover:bg-gray-100 rounded-md"
                    >
                        <Menu size={24} />
                    </button>
                </div>

                <div className="p-4 sm:p-6 lg:p-8">
                    {/* Search Bar */}
                    <div className="max-w-4xl mx-auto mb-8">
                        <div className="relative">
                            <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                                <Search className="h-5 w-5 text-gray-400" />
                            </div>
                            <input
                                type="text"
                                className="block w-full pl-11 pr-4 py-3 border border-gray-300 rounded-xl leading-5 bg-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent shadow-sm transition duration-150 ease-in-out"
                                placeholder="캠페인 검색 (키워드, 보상 등)"
                                value={keyword}
                                onChange={(e) => setKeyword(e.target.value)}
                            />
                        </div>
                    </div>

                    {/* Results Count & Active Filters Summary */}
                    <div className="flex flex-col sm:flex-row justify-between items-start sm:items-end mb-6 gap-4">
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
                            <div className="text-sm font-medium text-blue-600 bg-blue-50 px-3 py-1.5 rounded-full shrink-0">
                                총 {filtered.length}개 중 {visibleCampaigns.length}개 표시
                            </div>
                        </div>
                    </div>

                    {/* Grid */}
                    {visibleCampaigns.length > 0 ? (
                        <>
                            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
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
                                    setFilters(prev => ({
                                        ...prev,
                                        platforms: [],
                                        province: '',
                                        cities: [],
                                        categories: [],
                                        channels: [],
                                        minReward: 0,
                                        hideClosed: false
                                    }));
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
