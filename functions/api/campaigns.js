// Cloudflare Pages Function: GET /api/campaigns
// R2 버킷(바인딩 이름: DATA_BUCKET)의 gzip JSON을 그대로 내려준다.
// 크롤러(GitHub Actions)가 매시간 이 파일만 교체하므로 사이트 재배포는 필요 없다.
const OBJECT_KEY = 'v1/campaigns.json.gz';

export async function onRequestGet({ env }) {
  if (!env.DATA_BUCKET) {
    return new Response('R2 binding DATA_BUCKET is not configured', { status: 500 });
  }

  const object = await env.DATA_BUCKET.get(OBJECT_KEY);
  if (!object) {
    return new Response('Data not found', { status: 404 });
  }

  return new Response(object.body, {
    headers: {
      'Content-Type': 'application/json; charset=utf-8',
      'Content-Encoding': 'gzip',
      // 브라우저/엣지 캐시 5분: 크롤러 갱신 주기(1시간)보다 충분히 짧다
      'Cache-Control': 'public, max-age=300',
      ETag: object.httpEtag,
    },
  });
}
