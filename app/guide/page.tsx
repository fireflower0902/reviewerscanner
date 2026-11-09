import type { Metadata } from 'next';
import InfoPage from '../components/InfoPage';
import GuideContent, { GUIDE_SUBTITLE } from '../components/content/GuideContent';

export const metadata: Metadata = {
  title: '이용가이드 | 체험단 스캐너',
  description: '체험단 스캐너 사용법: 지역·카테고리·채널·키워드로 체험단 캠페인을 찾고, 원본 사이트에서 신청하는 방법을 안내합니다.',
};

export default function GuidePage() {
  return (
    <InfoPage current="guide" title="이용가이드" updated={GUIDE_SUBTITLE}>
      <GuideContent />
    </InfoPage>
  );
}
