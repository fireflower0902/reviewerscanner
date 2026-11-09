import type { Metadata } from 'next';
import InfoPage from '../components/InfoPage';
import TermsContent, { TERMS_UPDATED } from '../components/content/TermsContent';

export const metadata: Metadata = {
  title: '이용약관 | 체험단 스캐너',
  description: '체험단 스캐너 서비스 이용약관: 서비스의 성격, 정보의 정확성, 광고, 저작권, 문의 및 정정·삭제 요청 방법 등을 안내합니다.',
};

export default function TermsPage() {
  return (
    <InfoPage current="terms" title="이용약관" updated={TERMS_UPDATED}>
      <TermsContent />
    </InfoPage>
  );
}
