// 채널(활동 방식) 옆에 붙는 작은 아이콘. 각 서비스의 색·모양을 닮게 직접 그린 SVG (외부 이미지 사용 안 함)
const IG_GRADIENT = (
    <defs>
        <linearGradient id="ch-ig" x1="0" y1="24" x2="24" y2="0" gradientUnits="userSpaceOnUse">
            <stop offset="0" stopColor="#FEDA75" />
            <stop offset="0.3" stopColor="#FA7E1E" />
            <stop offset="0.55" stopColor="#D62976" />
            <stop offset="0.8" stopColor="#962FBF" />
            <stop offset="1" stopColor="#4F5BD5" />
        </linearGradient>
    </defs>
);

export default function ChannelIcon({ channel, size = 20 }: { channel: string; size?: number }) {
    const common = {
        width: size,
        height: size,
        viewBox: '0 0 24 24',
        'aria-hidden': true,
        className: 'shrink-0',
    } as const;

    switch (channel) {
        case '네이버 블로그':
            return (
                <svg {...common}>
                    <rect width="24" height="24" rx="6" fill="#03C75A" />
                    <path d="M7.2 17.5V6.5h2.7l4.3 6.3V6.5h2.6v11h-2.6l-4.4-6.4v6.4z" fill="#fff" />
                </svg>
            );
        case '네이버 클립':
            return (
                <svg {...common}>
                    <rect width="24" height="24" rx="6" fill="#03C75A" />
                    <circle cx="12" cy="12" r="6.3" fill="#fff" />
                    <path d="M10.4 8.9v6.2l5-3.1z" fill="#03C75A" />
                </svg>
            );
        case '인스타그램 피드':
            return (
                <svg {...common}>
                    {IG_GRADIENT}
                    <rect width="24" height="24" rx="6" fill="url(#ch-ig)" />
                    <rect x="5.5" y="5.5" width="13" height="13" rx="4" fill="none" stroke="#fff" strokeWidth="1.7" />
                    <circle cx="12" cy="12" r="3.1" fill="none" stroke="#fff" strokeWidth="1.7" />
                    <circle cx="16.1" cy="7.9" r="1" fill="#fff" />
                </svg>
            );
        case '인스타그램 릴스':
            return (
                <svg {...common}>
                    {IG_GRADIENT}
                    <rect width="24" height="24" rx="6" fill="url(#ch-ig)" />
                    <rect x="5.5" y="5.5" width="13" height="13" rx="4" fill="none" stroke="#fff" strokeWidth="1.7" />
                    <path d="M10.2 9.2v5.6l4.6-2.8z" fill="#fff" />
                </svg>
            );
        case '유튜브 동영상':
            return (
                <svg {...common}>
                    <rect width="24" height="24" rx="6" fill="#FF0000" />
                    <path d="M9.6 7.8v8.4l7-4.2z" fill="#fff" />
                </svg>
            );
        case '유튜브 숏츠':
            return (
                <svg {...common}>
                    <rect width="24" height="24" rx="6" fill="#FF0000" />
                    <rect x="8.2" y="4.8" width="7.6" height="14.4" rx="3.8" fill="#fff" />
                    <path d="M10.8 10v4l3.2-2z" fill="#FF0000" />
                </svg>
            );
        default:
            return null;
    }
}
