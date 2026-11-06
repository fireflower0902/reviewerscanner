// 30분마다 GitHub Actions 의 크롤러 워크플로를 workflow_dispatch 로 실행한다.
// 필요한 비밀값: GITHUB_TOKEN (fine-grained PAT, 이 저장소 Actions: Read and write)
const REPO = "fireflower0902/reviewerscanner";
const WORKFLOW = "crawler.yml";
const REF = "main";

async function dispatch(env) {
  const res = await fetch(
    `https://api.github.com/repos/${REPO}/actions/workflows/${WORKFLOW}/dispatches`,
    {
      method: "POST",
      headers: {
        Authorization: `Bearer ${env.GITHUB_TOKEN}`,
        Accept: "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "reviewerscanner-cron",
      },
      body: JSON.stringify({ ref: REF }),
    }
  );
  const text = res.status === 204 ? "" : await res.text();
  console.log(`dispatch -> ${res.status} ${text}`);
  return { status: res.status, text };
}

export default {
  async scheduled(event, env, ctx) {
    ctx.waitUntil(dispatch(env));
  },
  // 수동 확인용: 브라우저로 열면 상태만 알려줌(실행은 하지 않음)
  async fetch() {
    return new Response("reviewerscanner-cron ok (cron: every 30 minutes)");
  },
};
