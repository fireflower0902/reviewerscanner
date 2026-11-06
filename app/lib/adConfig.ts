// 하단 광고 설정 — 광고 종류를 바꾸려면 아래 `provider` 값만 바꾸면 된다.
//   'coupang' : 쿠팡 파트너스 (광고 바로 아래에 공정위 문구가 함께 표시됨)
//   'adsense' : 구글 애드센스 (승인 후 사용. 아직 연결 코드가 없음 — AdBar.tsx 참고)
//   'none'    : 광고 영역을 표시하지 않음

export type AdProvider = 'coupang' | 'adsense' | 'none';

export const AD_CONFIG = {
    provider: 'coupang' as AdProvider,

    // 쿠팡 파트너스 다이나믹 배너 (쿠팡 파트너스에서 발급받은 코드의 값 그대로)
    coupang: {
        id: 1047353,
        template: 'carousel',
        trackingCode: 'AF3489479',
        width: '680',
        height: '90',
        tsource: '',
    },

    // 애드센스 (승인 후 입력)
    adsense: {
        client: '',   // 예: 'ca-pub-0000000000000000'
        slot: '',     // 광고 단위 ID
    },

    // 공정위 문구 — 쿠팡일 때만 광고 바로 아래에 표시된다. (쿠팡 파트너스 가이드의 문구로 확정 필요)
    disclosure: '이 서비스는 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다.',
};
