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

export interface Campaign {
    platform: string;
    title: string;
    url: string;
    region: Region;
    category: string;
    reward: Reward;
    meta: Meta;
    image_url: string;
    stats?: {
        applicants: number;
        quota: number;
    };
}
