import CampaignList from './components/CampaignList';
import AdBar from './components/AdBar';
import Hero from './components/Hero';
import { FilterDrawerProvider } from './components/FilterDrawer';
import InstallGuideProvider from './components/InstallGuide';
import { InfoModalProvider } from './components/InfoModal';

export default function Home() {
  return (
    <FilterDrawerProvider>
    <InstallGuideProvider>
    <InfoModalProvider>
    <main className="min-h-screen bg-gray-50">
      {/* Hero Section (모바일에서는 오른쪽 끝에 필터 버튼) */}
      <Hero />

      {/* Main Content */}
      <div>
        <CampaignList />
      </div>

      {/* 하단 고정 광고 띠 (종류는 app/lib/adConfig.ts) */}
      <AdBar />
    </main>
    </InfoModalProvider>
    </InstallGuideProvider>
    </FilterDrawerProvider>
  );
}
