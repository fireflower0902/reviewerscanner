import Image from 'next/image';
import { Campaign } from '../types/campaign';
import { MapPin, Gift, Clock } from 'lucide-react';

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
                        sizes="(max-width: 640px) 50vw, (max-width: 1200px) 33vw, 25vw"
                        unoptimized={campaign.image_url.includes('cometoplay')}
                    />
                ) : (
                    <div className="flex h-full items-center justify-center text-gray-400 text-xs">
                        No Image
                    </div>
                )}
                <div className="absolute top-1.5 left-1.5 flex gap-1 flex-wrap max-w-[85%]">
                    <span className={`
            px-1.5 py-0.5 text-[10px] font-bold rounded-md text-white shadow-sm leading-tight
            ${campaign.platform === '강남맛집' ? 'bg-orange-500' :
                            campaign.platform === '리뷰노트' ? 'bg-blue-500' :
                                campaign.platform === '디너의여왕' ? 'bg-red-500' :
                                    campaign.platform === '서울오빠' ? 'bg-purple-500' :
                                        'bg-green-500'}`}>
                        {campaign.platform}
                    </span>
                    <span className="px-1.5 py-0.5 text-[10px] font-bold rounded-md bg-indigo-500 text-white shadow-sm leading-tight">
                        {campaign.category}
                    </span>
                </div>
                <div className="absolute bottom-1.5 right-1.5">
                    <span className="px-1.5 py-0.5 text-[10px] font-medium bg-black/60 text-white rounded backdrop-blur-sm flex items-center gap-0.5">
                        <Clock size={10} />
                        {campaign.meta.dday}
                    </span>
                </div>
            </div>

            <div className="p-2 sm:p-4">
                <div className="flex flex-wrap items-center gap-1 mb-1.5 text-[10px] sm:text-xs font-medium text-gray-500">
                    <span className="flex items-center gap-0.5 px-1 py-0.5 rounded bg-blue-50 text-blue-700 border border-blue-100 leading-tight">
                        {campaign.meta.type}
                    </span>
                    <span className="flex items-center gap-0.5 leading-tight">
                        <MapPin size={10} />
                        {campaign.region.normalized}
                    </span>
                </div>

                <h3 className="font-bold text-gray-900 line-clamp-2 mb-1.5 text-xs sm:text-sm group-hover:text-blue-600 transition-colors leading-snug">
                    {campaign.title}
                </h3>

                <div className="flex items-start gap-1.5 text-xs text-gray-600 bg-gray-50 p-1.5 rounded-lg mb-2 sm:mb-3">
                    <Gift size={12} className="mt-0.5 shrink-0 text-red-400" />
                    <p className="line-clamp-2 text-[10px] sm:text-xs">{campaign.reward.text}</p>
                </div>

                {campaign.stats && (
                    <div className="flex items-center justify-end text-[10px] sm:text-xs font-medium border-t border-gray-100 pt-2 mt-auto">
                        <div className="flex items-center gap-1 text-gray-600 bg-gray-50 px-1.5 py-0.5 rounded">
                            <span className="text-gray-400">👤</span>
                            <span>신청 <strong className="text-gray-900">{campaign.stats.applicants}</strong></span>
                            <span className="text-gray-300 mx-0.5">/</span>
                            <span className="text-gray-500">모집 {campaign.stats.quota}</span>
                        </div>
                    </div>
                )}
            </div>
        </a>
    );
}
