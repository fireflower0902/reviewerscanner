// 필터의 플랫폼 이름 옆에 붙는 작은 아이콘 (각 사이트가 공개한 파비콘/앱 아이콘을 64×64로 변환해 public/platform-icons/ 에 보관)
export const PLATFORM_ICONS: Record<string, string> = {
    '강남맛집': '/platform-icons/gangnam.png',
    '놀러와체험단': '/platform-icons/cometoplay.png',
    '디너의여왕': '/platform-icons/dinnerqueen.png',
    '레뷰': '/platform-icons/revu.png',
    '리뷰노트': '/platform-icons/reviewnote.png',
    '리뷰플레이스': '/platform-icons/reviewplace.png',
    '서울오빠': '/platform-icons/seouloppa.png',
    '오마이블로그': '/platform-icons/ohmyblog.png',
    '포블로그': '/platform-icons/fourblog.png',
};

// 카드 사진 위 플랫폼 배지 색. 각 사이트 아이콘의 대표색을 따라 사이트끼리 구분되게 한다. (bg, text 는 Tailwind 클래스)
export const PLATFORM_BADGE: Record<string, string> = {
    '강남맛집': 'bg-[#f97316] text-white',
    '놀러와체험단': 'bg-[#facc15] text-[#422006]',   // 노랑 배경이라 글자는 진한 갈색
    '디너의여왕': 'bg-[#ff4081] text-white',
    '레뷰': 'bg-[#8f01ff] text-white',
    '리뷰노트': 'bg-[#0a62a8] text-white',
    '리뷰플레이스': 'bg-[#e84250] text-white',
    '서울오빠': 'bg-[#5b93ff] text-white',
    '오마이블로그': 'bg-[#5a69ae] text-white',
    '포블로그': 'bg-[#a78bda] text-white',
};
export const PLATFORM_BADGE_FALLBACK = 'bg-gray-500 text-white';
