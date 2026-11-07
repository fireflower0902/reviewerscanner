export interface Region {
    province: string;
    city: string;
    normalized: string;
}

export interface Reward {
    text: string;
    value: number;
}

export interface Meta {
    type: string;
    dday: string;
}

export interface Location {
    lat: number;
    lng: number;
    address?: string;
    name?: string;
}

export interface Campaign {
    platform: string;
    title: string;
    url: string;
    region: Region;
    category: string;
    reward: Reward;
    meta: Meta;
    image_url: string;
    location?: Location;   // 가게 위치(지도용). 사이트가 좌표를 제공하는 경우에만 있음
    stats?: {
        applicants: number;
        quota: number;
    };
}
