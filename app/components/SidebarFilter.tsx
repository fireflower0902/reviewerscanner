'use client';

import { useMemo } from 'react';
import { Campaign } from '../types/campaign';
import { X, Check } from 'lucide-react';

interface SidebarFilterProps {
    campaigns: Campaign[];
    filters: {
        platforms: string[];
        province: string;
        cities: string[]; // Changed to array for multi-select
        categories: string[]; // New: Categories
        channels: string[]; // New: Blog, Insta, YouTube
        minReward: number; // New: Min reward
        hideClosed: boolean; // New: Hide closed/past deadline
    };
    onFilterChange: (newFilters: any) => void;
    isOpen?: boolean;
    onClose?: () => void;
}

export default function SidebarFilter({
    campaigns,
    filters,
    onFilterChange,
    isOpen,
    onClose
}: SidebarFilterProps) {
    // 1. Extract Unique Platforms
    const allPlatforms = useMemo(() => {
        const platforms = new Set(campaigns.map(c => c.platform));
        return Array.from(platforms).sort();
    }, [campaigns]);

    // 2. Extract Provinces & Cities hierarchy
    const regionHierarchy = useMemo(() => {
        const hierarchy: Record<string, Set<string>> = {};

        campaigns.forEach(c => {
            const p = c.region.province;
            const city = c.region.city;

            // Filter out invalid provinces
            if (!p || p === 'undefined' || p === 'null') return;

            if (!hierarchy[p]) {
                hierarchy[p] = new Set();
            }
            // Filter out invalid cities and avoid duplicate if city == province
            if (city && city !== p && city !== 'undefined' && city !== 'null') {
                hierarchy[p].add(city);
            }
        });

        const sorted: Record<string, string[]> = {};
        Object.keys(hierarchy).sort().forEach(p => {
            sorted[p] = Array.from(hierarchy[p]).sort();
        });

        return sorted;
    }, [campaigns]);

    // 3. Categories & Channels
    const categories = ['음식점', '뷰티', '여행', '숙박', '문화', '배달', '운동', '레저', '생활', '포장', '반려동물', '식품', '유아동', '기타'];
    const channels = ['네이버 블로그', '인스타그램 릴스', '인스타그램 피드', '유튜브 동영상', '유튜브 숏츠', '네이버 클립'];

    // Handlers
    const togglePlatform = (platform: string) => {
        const current = filters.platforms;
        const next = current.includes(platform)
            ? current.filter(p => p !== platform)
            : [...current, platform];
        onFilterChange({ ...filters, platforms: next });
    };

    const setProvince = (p: string) => {
        if (p === filters.province) return;
        onFilterChange({ ...filters, province: p, cities: [] }); // Reset cities
    };

    const toggleCity = (city: string) => {
        const current = filters.cities;
        const next = current.includes(city)
            ? current.filter(c => c !== city)
            : [...current, city];
        onFilterChange({ ...filters, cities: next });
    };

    const toggleCategory = (category: string) => {
        const current = filters.categories || [];
        const next = current.includes(category)
            ? current.filter(c => c !== category)
            : [...current, category];
        onFilterChange({ ...filters, categories: next });
    };

    const toggleChannel = (channel: string) => {
        const current = filters.channels;
        const next = current.includes(channel)
            ? current.filter(c => c !== channel)
            : [...current, channel];
        onFilterChange({ ...filters, channels: next });
    };

    const formatCurrency = (val: number) => {
        return new Intl.NumberFormat('ko-KR').format(val);
    };

    return (
        <>
            {/* Mobile Overlay */}
            <div
                className={`fixed inset-0 bg-black/50 z-40 lg:hidden ${isOpen ? 'block' : 'hidden'}`}
                onClick={onClose}
            />

            {/* Sidebar Container */}
            <aside className={`
        fixed top-0 left-0 bottom-0 z-50 w-72 bg-white shadow-xl transform transition-transform duration-300 ease-in-out lg:translate-x-0 lg:static lg:shadow-none lg:z-auto lg:h-auto lg:w-72 lg:block border-r border-gray-200 overflow-y-auto
        ${isOpen ? 'translate-x-0' : '-translate-x-full'}
      `}>
                <div className="p-5 space-y-8">
                    <div className="flex justify-between items-center lg:hidden">
                        <h2 className="text-xl font-bold text-gray-900">필터 설정</h2>
                        <button onClick={onClose} className="p-2 -mr-2 text-gray-500 hover:bg-gray-100 rounded-full">
                            <X size={20} />
                        </button>
                    </div>

                    {/* Section: Platform */}
                    <div>
                        <h3 className="text-sm font-semibold text-gray-900 uppercase tracking-wider mb-3">
                            플랫폼
                        </h3>
                        <div className="space-y-3">
                            <label className="flex items-center space-x-3 cursor-pointer group">
                                <div className={`
                    w-6 h-6 rounded border flex items-center justify-center transition-colors
                    ${filters.platforms.length === 0
                                        ? 'bg-blue-600 border-blue-600'
                                        : 'border-gray-300 group-hover:border-blue-400'}
                  `}>
                                    {filters.platforms.length === 0 && <Check size={14} className="text-white" />}
                                </div>
                                <input
                                    type="checkbox"
                                    className="hidden"
                                    checked={filters.platforms.length === 0}
                                    onChange={() => onFilterChange({ ...filters, platforms: [] })}
                                />
                                <span className={`text-base ${filters.platforms.length === 0 ? 'text-gray-900 font-medium' : 'text-gray-600'}`}>
                                    전체
                                </span>
                            </label>
                            {allPlatforms.map(platform => (
                                <label key={platform} className="flex items-center space-x-3 cursor-pointer group">
                                    <div className={`
                    w-6 h-6 rounded border flex items-center justify-center transition-colors
                    ${filters.platforms.includes(platform)
                                            ? 'bg-blue-600 border-blue-600'
                                            : 'border-gray-300 group-hover:border-blue-400'}
                  `}>
                                        {filters.platforms.includes(platform) && <Check size={14} className="text-white" />}
                                    </div>
                                    <input
                                        type="checkbox"
                                        className="hidden"
                                        checked={filters.platforms.includes(platform)}
                                        onChange={() => togglePlatform(platform)}
                                    />
                                    <span className={`text-base ${filters.platforms.includes(platform) ? 'text-gray-900 font-medium' : 'text-gray-600'}`}>
                                        {platform}
                                    </span>
                                </label>
                            ))}
                        </div>
                    </div>

                    {/* Section: Category */}
                    <div>
                        <h3 className="text-sm font-semibold text-gray-900 uppercase tracking-wider mb-3">
                            카테고리
                        </h3>
                        <div className="flex flex-wrap gap-2">
                            <button
                                onClick={() => onFilterChange({ ...filters, categories: [] })}
                                className={`
                    px-3.5 py-2 rounded-lg text-sm font-medium border transition-all
                    ${(!filters.categories || filters.categories.length === 0)
                                        ? 'bg-blue-50 text-blue-700 border-blue-200 ring-1 ring-blue-200'
                                        : 'bg-white text-gray-600 border-gray-200 hover:border-gray-300'}
                  `}
                            >
                                전체
                            </button>
                            {categories.map(category => (
                                <button
                                    key={category}
                                    onClick={() => toggleCategory(category)}
                                    className={`
                    px-3.5 py-2 rounded-lg text-sm font-medium border transition-all
                    ${(filters.categories || []).includes(category)
                                            ? 'bg-blue-50 text-blue-700 border-blue-200 ring-1 ring-blue-200'
                                            : 'bg-white text-gray-600 border-gray-200 hover:border-gray-300'}
                  `}
                                >
                                    {category}
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Section: Channel */}
                    <div>
                        <h3 className="text-sm font-semibold text-gray-900 uppercase tracking-wider mb-3">
                            채널 (활동 방식)
                        </h3>
                        <div className="flex flex-wrap gap-2">
                            <button
                                onClick={() => onFilterChange({ ...filters, channels: [] })}
                                className={`
                    px-3.5 py-2 rounded-lg text-sm font-medium border transition-all
                    ${(!filters.channels || filters.channels.length === 0)
                                        ? 'bg-purple-50 text-purple-700 border-purple-200 ring-1 ring-purple-200'
                                        : 'bg-white text-gray-600 border-gray-200 hover:border-gray-300'}
                  `}
                            >
                                전체
                            </button>
                            {channels.map(channel => (
                                <button
                                    key={channel}
                                    onClick={() => toggleChannel(channel)}
                                    className={`
                    px-3.5 py-2 rounded-lg text-sm font-medium border transition-all
                    ${filters.channels.includes(channel)
                                            ? 'bg-purple-50 text-purple-700 border-purple-200 ring-1 ring-purple-200'
                                            : 'bg-white text-gray-600 border-gray-200 hover:border-gray-300'}
                  `}
                                >
                                    {channel}
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Section: Region */}
                    <div>
                        <h3 className="text-sm font-semibold text-gray-900 uppercase tracking-wider mb-3">
                            지역 선택
                        </h3>

                        {/* Province Select */}
                        <div className="mb-3">
                            <label className="block text-xs font-medium text-gray-500 mb-1">시/도</label>
                            <select
                                value={filters.province}
                                onChange={(e) => setProvince(e.target.value)}
                                className="w-full bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block p-2.5"
                            >
                                <option value="">전체</option>
                                {Object.keys(regionHierarchy).map(p => (
                                    <option key={p} value={p}>{p}</option>
                                ))}
                            </select>
                        </div>

                        {/* City Select (Multi-select Chips) */}
                        {filters.province && regionHierarchy[filters.province] && regionHierarchy[filters.province].length > 0 && (
                            <div className="animate-in fade-in slide-in-from-top-2 duration-200">
                                <label className="block text-xs font-medium text-gray-500 mb-2">
                                    상세 지역 (다중 선택 가능)
                                </label>
                                <div className="flex flex-wrap gap-2 max-h-48 overflow-y-auto p-1">
                                    {/* 전체 버튼 */}
                                    <button
                                        onClick={() => onFilterChange({ ...filters, cities: [] })}
                                        className={`
                         px-3.5 py-2 rounded-full text-sm border transition-colors
                         ${filters.cities.length === 0
                                                ? 'bg-blue-600 text-white border-blue-600 shadow-sm'
                                                : 'bg-white text-gray-600 border-gray-200 hover:bg-gray-50'}
                       `}
                                    >
                                        전체
                                    </button>
                                    {regionHierarchy[filters.province].map(city => (
                                        <button
                                            key={city}
                                            onClick={() => toggleCity(city)}
                                            className={`
                         px-3.5 py-2 rounded-full text-sm border transition-colors
                         ${filters.cities.includes(city)
                                                    ? 'bg-blue-600 text-white border-blue-600 shadow-sm'
                                                    : 'bg-white text-gray-600 border-gray-200 hover:bg-gray-50'}
                       `}
                                        >
                                            {city}
                                        </button>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>

                    {/* Section: Reward */}
                    <div>
                        <h3 className="text-sm font-semibold text-gray-900 uppercase tracking-wider mb-3">
                            최소 보상 금액 <span className="text-blue-600 text-xs ml-1">{formatCurrency(filters.minReward)}원 이상</span>
                        </h3>
                        <div className="px-1">
                            <input
                                type="range"
                                min="0"
                                max="100000"
                                step="5000"
                                value={filters.minReward}
                                onChange={(e) => onFilterChange({ ...filters, minReward: Number(e.target.value) })}
                                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
                            />
                        </div>
                        <div className="flex justify-between text-xs text-gray-400 mt-1">
                            <span>0원</span>
                            <span>10만원+</span>
                        </div>
                    </div>

                    {/* Section: Options */}
                    <div>
                        <h3 className="text-sm font-semibold text-gray-900 uppercase tracking-wider mb-2">
                            기타 옵션
                        </h3>
                        <label className="flex items-center space-x-3 cursor-pointer">
                            <input
                                type="checkbox"
                                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                                checked={filters.hideClosed}
                                onChange={(e) => onFilterChange({ ...filters, hideClosed: e.target.checked })}
                            />
                            <span className="text-sm text-gray-700">마감된 캠페인 숨기기 (D-Day 지남)</span>
                        </label>
                    </div>

                    {/* Footer: Reset */}
                    <div className="pt-4 border-t border-gray-100">
                        <button
                            onClick={() => onFilterChange({
                                platforms: [],
                                province: '',
                                cities: [],
                                categories: [],
                                channels: [],
                                minReward: 0,
                                hideClosed: false
                            })}
                            className="w-full py-2 text-sm text-gray-500 hover:text-gray-900 underline decoration-gray-300 underline-offset-4 transition-colors"
                        >
                            필터 초기화
                        </button>
                    </div>

                </div>
            </aside>
        </>
    );
}
