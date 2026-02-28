import Image from 'next/image';
import { Campaign } from '../types/campaign';
import { MapPin, Gift, Clock, Truck, Home } from 'lucide-react';

interface CampaignCardProps {
    campaign: Campaign;
}

export default function CampaignCard({ campaign }: CampaignCardProps) {
    return (
        <a
            href={campaign.url}
            target="_blank"
            rel="noopener noreferrer"
            className="group block bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden hover:shadow-md transition-shadow duration-200"
        >
            <div className="relative aspect-[4/3] w-full overflow-hidden bg-gray-100">
                {campaign.image_url ? (
                    <Image
                        src={campaign.image_url}
                        alt={campaign.title}
                        fill
                        className="object-cover group-hover:scale-105 transition-transform duration-300"
                        sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
                    />
                ) : (
                    <div className="flex h-full items-center justify-center text-gray-400">
                        No Image
                    </div>
                )}
                <div className="absolute top-2 left-2 flex gap-1">
                    <span className={`
            px-2 py-1 text-xs font-bold rounded-md text-white shadow-sm
            ${campaign.platform === '강남맛집' ? 'bg-orange-500' :
                            campaign.platform === '리뷰노트' ? 'bg-blue-500' :
                                campaign.platform === '디너의여왕' ? 'bg-red-500' :
                                    campaign.platform === '서울오빠' ? 'bg-purple-500' :
                                        'bg-green-500'}
          `}>
                        {campaign.platform}
                    </span>
                    <span className="px-2 py-1 text-xs font-bold rounded-md bg-indigo-500 text-white shadow-sm">
                        {campaign.category}
                    </span>
                </div>
                <div className="absolute bottom-2 right-2">
                    <span className="px-2 py-1 text-xs font-medium bg-black/60 text-white rounded backdrop-blur-sm flex items-center gap-1">
                        <Clock size={12} />
                        {campaign.meta.dday}
                    </span>
                </div>
            </div>

            <div className="p-4">
                <div className="flex flex-wrap items-center gap-2 mb-2 text-xs font-medium text-gray-500">
                    <span className="flex items-center gap-1 px-1.5 py-0.5 rounded bg-blue-50 text-blue-700 border border-blue-100">
                        {campaign.meta.type}
                    </span>
                    <span className="flex items-center gap-1">
                        <MapPin size={12} />
                        {campaign.region.normalized}
                    </span>
                </div>

                <h3 className="font-bold text-gray-900 line-clamp-2 mb-2 group-hover:text-blue-600 transition-colors">
                    {campaign.title}
                </h3>

                <div className="flex items-start gap-2 text-sm text-gray-600 bg-gray-50 p-2 rounded-lg mb-3">
                    <Gift size={14} className="mt-1 shrink-0 text-red-400" />
                    <p className="line-clamp-2 text-xs">{campaign.reward.text}</p>
                </div>

                {/* 하단 통계(지원자/정원 현황) 영역 추가 */}
                {campaign.stats && (
                    <div className="flex items-center justify-end text-xs font-medium border-t border-gray-100 pt-3 mt-auto">
                        <div className="flex items-center gap-1 text-gray-600 bg-gray-50 px-2 py-1 rounded">
                            <span className="text-gray-400">👤</span>
                            <span>신청 <strong className="text-gray-900">{campaign.stats.applicants}</strong></span>
                            <span className="text-gray-300 mx-1">/</span>
                            <span className="text-gray-500">모집 {campaign.stats.quota}</span>
                        </div>
                    </div>
                )}
            </div>
        </a>
    );
}
