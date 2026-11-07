import { Utensils, Sparkles, Plane, Drama, Dumbbell, House, PawPrint, Baby, Ellipsis } from 'lucide-react';
import type { LucideIcon } from 'lucide-react';

// 카테고리 옆 작은 아이콘: 색 그라데이션 타일 + 흰색 아이콘 (채널 아이콘과 같은 스타일)
const CATEGORY_ICONS: Record<string, { Icon: LucideIcon; tile: string }> = {
    '음식점': { Icon: Utensils, tile: 'from-orange-400 to-red-500' },
    '뷰티': { Icon: Sparkles, tile: 'from-pink-400 to-rose-500' },
    '여행/숙박': { Icon: Plane, tile: 'from-sky-400 to-blue-500' },
    '문화/레저': { Icon: Drama, tile: 'from-violet-400 to-purple-600' },
    '운동': { Icon: Dumbbell, tile: 'from-green-400 to-emerald-600' },
    '생활': { Icon: House, tile: 'from-amber-400 to-amber-600' },
    '반려동물': { Icon: PawPrint, tile: 'from-amber-700 to-orange-900' },
    '유아동': { Icon: Baby, tile: 'from-cyan-400 to-teal-500' },
    '기타': { Icon: Ellipsis, tile: 'from-gray-400 to-slate-500' },
};

export default function CategoryIcon({ category, size = 20 }: { category: string; size?: number }) {
    const entry = CATEGORY_ICONS[category];
    if (!entry) return null;
    const { Icon, tile } = entry;
    return (
        <span
            aria-hidden="true"
            className={`flex shrink-0 items-center justify-center rounded-md bg-gradient-to-br ${tile}`}
            style={{ width: size, height: size }}
        >
            <Icon size={Math.round(size * 0.62)} strokeWidth={2.3} color="#fff" />
        </span>
    );
}
