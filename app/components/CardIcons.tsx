// 캠페인 카드의 지역·보상·신청자 아이콘. 단색 선 아이콘 대신 은은한 그라데이션을 쓴 2톤 SVG.
type IconProps = { size?: number; className?: string };

const base = (size: number, className?: string) =>
    ({ width: size, height: size, viewBox: '0 0 24 24', 'aria-hidden': true, className: `shrink-0 ${className ?? ''}` }) as const;

/** 지역: 파랑→인디고 핀 + 흰 점 */
export function LocationIcon({ size = 14, className }: IconProps) {
    return (
        <svg {...base(size, className)}>
            <defs>
                <linearGradient id="ci-loc" x1="12" y1="2" x2="12" y2="22" gradientUnits="userSpaceOnUse">
                    <stop offset="0" stopColor="#60A5FA" />
                    <stop offset="1" stopColor="#4F46E5" />
                </linearGradient>
            </defs>
            <path
                d="M12 2C7.6 2 4 5.5 4 9.8c0 5.4 6.2 11 7.3 12a1 1 0 0 0 1.4 0c1.1-1 7.3-6.6 7.3-12C20 5.5 16.4 2 12 2z"
                fill="url(#ci-loc)"
            />
            <circle cx="12" cy="9.8" r="3.3" fill="#fff" />
        </svg>
    );
}

/** 보상: 코랄 선물상자 + 금빛 리본 */
export function RewardIcon({ size = 16, className }: IconProps) {
    return (
        <svg {...base(size, className)}>
            <defs>
                <linearGradient id="ci-gift-body" x1="12" y1="10" x2="12" y2="21.5" gradientUnits="userSpaceOnUse">
                    <stop offset="0" stopColor="#FB7185" />
                    <stop offset="1" stopColor="#E11D48" />
                </linearGradient>
                <linearGradient id="ci-gift-lid" x1="12" y1="7" x2="12" y2="11" gradientUnits="userSpaceOnUse">
                    <stop offset="0" stopColor="#FDA4AF" />
                    <stop offset="1" stopColor="#FB7185" />
                </linearGradient>
            </defs>
            <rect x="4.2" y="10.2" width="15.6" height="11.3" rx="2.2" fill="url(#ci-gift-body)" />
            <rect x="2.8" y="7" width="18.4" height="4.4" rx="1.8" fill="url(#ci-gift-lid)" />
            <rect x="10.7" y="7" width="2.6" height="14.5" fill="#FDE68A" />
            <path d="M12 7C10.2 7 8.2 6.6 7.6 5.2 7 3.8 8.2 2.6 9.7 3.1 11.3 3.6 12 5.4 12 7z" fill="#FBBF24" />
            <path d="M12 7c1.8 0 3.8-.4 4.4-1.8.6-1.4-.6-2.6-2.1-2.1C12.7 3.6 12 5.4 12 7z" fill="#FBBF24" />
        </svg>
    );
}

/** 신청자: 겹친 두 사람(앞: 파랑→인디고, 뒤: 연한 보라) */
export function ApplicantIcon({ size = 14, className }: IconProps) {
    return (
        <svg {...base(size, className)}>
            <defs>
                <linearGradient id="ci-ppl" x1="9" y1="5" x2="9" y2="20.5" gradientUnits="userSpaceOnUse">
                    <stop offset="0" stopColor="#60A5FA" />
                    <stop offset="1" stopColor="#4F46E5" />
                </linearGradient>
            </defs>
            <circle cx="16.6" cy="8.6" r="2.7" fill="#C7D2FE" />
            <path d="M15.2 14.4c3.4-.4 6.4 1.4 6.4 4.6 0 .8-.6 1.4-1.4 1.4h-4.1c.4-1.9-.1-4-.9-6z" fill="#C7D2FE" />
            <circle cx="9" cy="8" r="3.5" fill="url(#ci-ppl)" />
            <path d="M2.4 19.2c0-3.5 2.9-5.6 6.6-5.6s6.6 2.1 6.6 5.6c0 .8-.6 1.4-1.4 1.4H3.8c-.8 0-1.4-.6-1.4-1.4z" fill="url(#ci-ppl)" />
        </svg>
    );
}
