import CampaignList from './components/CampaignList';

export default function Home() {
  return (
    <main className="min-h-screen bg-gray-50">
      {/* Hero Section */}
      <div className="bg-gradient-to-r from-blue-600 to-indigo-700 text-white px-4 overflow-visible flex flex-col items-center justify-center pt-2 pb-10 md:pt-8 md:pb-8">
        <div className="max-w-7xl mx-auto text-center">
          <h1 className="text-2xl md:text-3xl font-extrabold tracking-tight mb-1 md:mb-2">
            체험단 스캐너
          </h1>
          {/* 모바일에서는 설명 문구 숨김 */}
          <p className="hidden md:block text-sm md:text-base text-blue-100 max-w-2xl mx-auto">
            모든 체험단을 한눈에. 지역별, 보상별 맞춤 검색.
          </p>
        </div>
      </div>

      {/* Main Content */}
      <div className="-mt-8">
        <CampaignList />
      </div>
    </main>
  );
}
