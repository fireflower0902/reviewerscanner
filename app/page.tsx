import { Campaign } from './types/campaign';
import CampaignList from './components/CampaignList';
import { doc, getDoc } from 'firebase/firestore';
import { db } from './lib/firebase';

export const revalidate = 60; // 초 단위 캐싱, 원할 시 0으로 하여 실시간 적용 가능

async function getCampaigns(): Promise<Campaign[]> {
  try {
    // 1. 메타데이터 (총 청크 개수) 확인
    const statusRef = doc(db, 'metrics', 'status');
    const statusSnap = await getDoc(statusRef);

    if (!statusSnap.exists()) {
      return [];
    }

    const totalChunks = statusSnap.data().total_chunks || 0;
    if (totalChunks === 0) return [];

    // 2. 청크들을 병렬로 비동기 호출 (속도 최적화 🚀)
    const chunkPromises = [];
    for (let i = 0; i < totalChunks; i++) {
      const chunkRef = doc(db, 'campaigns_chunks', `chunk_${i}`);
      chunkPromises.push(getDoc(chunkRef));
    }

    const chunkSnaps = await Promise.all(chunkPromises);

    // 3. 청크 데이터(items 배열) 모두 합치기
    const allCampaigns: Campaign[] = [];
    chunkSnaps.forEach((snap) => {
      if (snap.exists()) {
        const data = snap.data();
        if (data.items && Array.isArray(data.items)) {
          allCampaigns.push(...(data.items as Campaign[]));
        }
      }
    });

    return allCampaigns;
  } catch (error) {
    console.error("Failed to fetch campaigns from Firebase Firestore:", error);
    return [];
  }
}

export default async function Home() {
  const campaigns = await getCampaigns();

  return (
    <main className="min-h-screen bg-gray-50">
      {/* Hero Section */}
      <div className="bg-gradient-to-r from-blue-600 to-indigo-700 text-white px-4 overflow-visible flex flex-col items-center justify-center pt-6 pb-14 md:pt-8 md:pb-14">
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
        <CampaignList initialCampaigns={campaigns} />
      </div>
    </main>
  );
}
