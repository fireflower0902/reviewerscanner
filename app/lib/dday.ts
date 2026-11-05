// 마감 표기 보정: 데이터는 수집 시점 기준으로 "5일 남음"처럼 저장되어 있으므로,
// 수집 이후 날짜가 바뀐 만큼(한국 시간 기준) 화면에서 줄여서 보여준다.

const KST_OFFSET_MS = 9 * 60 * 60 * 1000;

function kstDateString(d: Date): string {
    return new Date(d.getTime() + KST_OFFSET_MS).toISOString().slice(0, 10);
}

/** generatedAt(ISO)부터 now까지 한국 시간 기준으로 며칠이 지났는지 */
export function kstDaysPassed(generatedAtIso: string, now: Date = new Date()): number {
    const generated = new Date(generatedAtIso);
    if (isNaN(generated.getTime())) return 0;
    const diffMs = Date.parse(kstDateString(now)) - Date.parse(kstDateString(generated));
    return Math.max(0, Math.round(diffMs / 86400000));
}

/** 마감 표기를 daysPassed일만큼 보정. 이미 마감이 지났으면 null(목록에서 제외) */
export function shiftDday(dday: string, daysPassed: number): string | null {
    if (daysPassed <= 0 || !dday) return dday;
    const m = dday.match(/(\d+)\s*일\s*남음/);
    if (m) {
        const remain = parseInt(m[1], 10) - daysPassed;
        if (remain < 0) return null;
        return remain === 0 ? '오늘까지' : `${remain}일 남음`;
    }
    if (dday.includes('오늘')) return null; // '오늘까지', '오늘마감' — 하루라도 지나면 마감
    return dday;
}

/** fetch 응답을 JSON으로 읽는다. 서버/중간 단계 설정 때문에 gzip이 풀리지 않고 도착해도(앞 2바이트 1f 8b) 직접 해제한다. */
export async function readJsonMaybeGzip<T>(res: Response): Promise<T> {
    const bytes = new Uint8Array(await res.arrayBuffer());
    let text: string;
    if (bytes.length > 2 && bytes[0] === 0x1f && bytes[1] === 0x8b && typeof DecompressionStream !== 'undefined') {
        const stream = new Blob([bytes]).stream().pipeThrough(new DecompressionStream('gzip'));
        text = await new Response(stream).text();
    } else {
        text = new TextDecoder().decode(bytes);
    }
    return JSON.parse(text) as T;
}
