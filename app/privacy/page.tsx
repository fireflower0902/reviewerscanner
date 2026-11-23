import type { Metadata } from 'next';
import InfoPage, { Section } from '../components/InfoPage';

const title = '개인정보처리방침';

export const metadata: Metadata = {
    title: `${title} | 체험단 스캐너`,
    description: '체험단 스캐너 웹과 안드로이드 앱의 개인정보 처리 및 권리 행사 방법을 안내합니다.',
    alternates: { canonical: '/privacy' },
};

export default function PrivacyPage() {
    return (
        <InfoPage current="privacy" title={title} updated="시행일: 2026년 11월 23일">
            <p>이 방침은 체험단 스캐너 웹사이트와 해당 웹서비스를 제공하는 안드로이드 앱에 적용됩니다.</p>
            <Section title="1. 처리하는 정보와 이용 목적">
                <p>캠페인 목록, 검색, 필터는 회원가입 없이 이용할 수 있습니다. 검색어와 필터 선택은 기기에서 목록을 좁히는 데 사용됩니다.</p>
                <p>서비스 접속 시 호스팅 및 콘텐츠 전송을 담당하는 Cloudflare가 IP 주소, 브라우저 정보, 요청 주소와 시각 등 접속 정보를 서비스 제공, 보안 및 오류 대응을 위해 처리할 수 있습니다. 외부 서버에서 캠페인 이미지를 불러올 때에도 해당 서버에 IP 주소 등 요청 정보가 전달될 수 있습니다.</p>
                <p>이메일로 문의하면 발신 이메일 주소와 본문 및 첨부파일에 포함된 정보를 문의 확인과 답변에 사용합니다.</p>
            </Section>
            <Section title="2. 광고와 외부 사이트">
                <p>쿠팡 파트너스 배너가 표시되는 화면에서는 배너 제공을 위해 쿠팡 광고 서버가 IP 주소, 브라우저 정보 및 쿠키 등을 처리할 수 있습니다. 배너를 선택하면 쿠팡이 광고 유입 및 구매 성과를 확인할 수 있습니다.</p>
                <p>캠페인 링크를 열어 외부 사이트에서 체험단에 신청하거나 쿠팡에서 상품을 구매하는 경우, 해당 사이트의 개인정보처리방침이 적용됩니다. 브라우저 설정에서 쿠키를 관리할 수 있습니다.</p>
            </Section>
            <Section title="3. 보유 및 파기">
                <p>문의 이메일은 답변 및 관련 이슈 처리에 필요한 기간 동안 보관하고, 처리 목적이 달성되면 삭제합니다. 법령에 따라 보존해야 하는 경우 해당 기간 동안 보관합니다. 외부 서비스가 직접 처리하는 정보의 보유 기간은 각 서비스의 정책에 따릅니다.</p>
            </Section>
            <Section title="4. 권리 행사 및 문의">
                <p>개인정보 열람, 정정, 삭제, 처리정지 요청과 개인정보 관련 문의는 <a className="break-all text-blue-700 underline" href="mailto:reviewerscanner@gmail.com">reviewerscanner@gmail.com</a>으로 보내주세요.</p>
            </Section>
            <Section title="5. 방침 변경">
                <p>방침을 변경하면 이 페이지에 변경된 내용과 시행일을 공개합니다.</p>
            </Section>
        </InfoPage>
    );
}
