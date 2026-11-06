// Cloudflare Pages Function: GET /api/status
// 마지막 크롤링의 사이트별 결과(성공/실패/제한초과, 건수, 소요시간)를 보여준다. GitHub 로그인 없이 원인을 볼 수 있게 한다.
// 데이터는 크롤러가 R2의 v1/run_report.json 으로 남긴다. 민감 정보는 담지 않는다.
export async function onRequestGet({ env }) {
  if (!env.DATA_BUCKET) {
    return new Response('R2 binding DATA_BUCKET is not configured', { status: 500 });
  }
  const object = await env.DATA_BUCKET.get('v1/run_report.json');
  if (!object) {
    return new Response(JSON.stringify({ message: 'run report not found yet' }), {
      status: 404,
      headers: { 'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'no-store' },
    });
  }
  return new Response(object.body, {
    headers: { 'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'no-store' },
  });
}
