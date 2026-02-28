import fs from 'fs';
import path from 'path';
import { Campaign } from './types/campaign';
import CampaignList from './components/CampaignList';

async function getCampaigns(): Promise<Campaign[]> {
  // Server-side file read
  // In production, this might be an API call or DB query
  const filePath = path.join(process.cwd(), 'public', 'campaigns.json');
  try {
    const fileContents = fs.readFileSync(filePath, 'utf8');
    return JSON.parse(fileContents);
  } catch (error) {
    console.error("Failed to read campaigns.json", error);
    return [];
  }
}

export default async function Home() {
  const campaigns = await getCampaigns();

  return (
    <main className="min-h-screen bg-gray-50">
      {/* Hero Section */}
      <div className="bg-gradient-to-r from-blue-600 to-indigo-700 text-white pb-12 pt-16 px-4">
        <div className="max-w-7xl mx-auto text-center">
          <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight mb-4 animate-in fade-in slide-in-from-bottom-4 duration-700">
            리뷰어 스캐너
          </h1>
          <p className="text-xl md:text-2xl text-blue-100 max-w-2xl mx-auto">
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
