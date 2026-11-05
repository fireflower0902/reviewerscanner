# 체험단스캐너 (구 리뷰어스캐너) — 프로젝트 현황 & 이력 정리

> 작성일: 2026-11-04 (코드·git 이력을 직접 확인해 작성)
> 저장소: https://github.com/fireflower0902/reviewerscanner (branch: `main`)

---

## 1. 한 줄 요약

한국 체험단 사이트 **9곳**의 캠페인을 크롤링해 Firestore에 올리고, Next.js 웹에서 지역·카테고리·채널·보상으로 한 번에 필터링하는 통합 검색 서비스. (스카이스캐너식 UX가 목표)

## 2. 아키텍처

```
[GitHub Actions 매시간 cron]
   └ crawler/aggregator.py
        ├ crawlers/*.py  (9개 사이트, 동시 5개 제한)
        ├ region_mapper.py / category_mapper.py / helpers.py (정규화)
        ├ public/campaigns.json 저장 (git ignore됨)
        └ firebase_chunk_client.py → Firestore (chunk_N 문서, 1000건/청크)
                                        │
[Vercel] Next.js 16 (SSR, revalidate 60s) ┘ → CampaignList + SidebarFilter + CampaignCard
```

| 영역 | 스택 |
|---|---|
| 프론트 | Next.js 16.1.6 (App Router) · React 19 · TypeScript · Tailwind 4 · lucide-react |
| 크롤러 | Python 3.11 · Playwright(async) · BeautifulSoup4 · firebase-admin |
| DB | Firebase Firestore (projectId `reviewerscanner-dev`, nam5) |
| 배포/자동화 | Vercel(프론트), GitHub Actions(크롤러, `0 * * * *` + 수동 실행) |

## 3. 디렉터리 안내

| 경로 | 설명 |
|---|---|
| `app/` | 프론트엔드. `page.tsx`(SSR, Firestore 청크 병렬 fetch), `components/{CampaignList,CampaignCard,SidebarFilter}.tsx`, `types/campaign.ts`, `lib/firebase.ts` |
| `crawler/aggregator.py` | 오케스트레이터 (현재 작업트리 78줄 — 아래 §6 참고) |
| `crawler/crawlers/` | 사이트별 크롤러 9개 (**아직 커밋 안 됨**) |
| `crawler/helpers.py` | 공통 함수: `normalize_reward`, `map_channel`, `parse_region_from_title` 등 (**미커밋**) |
| `crawler/region_mapper.py` | 17개 시도, 모호 도시, 랜드마크→시/구 매핑 |
| `crawler/category_mapper.py` | 플랫폼별 카테고리 → 표준 14종 매핑 |
| `crawler/firebase_chunk_client.py` | Firestore 청크 업로드 (현재 사용 중) |
| `crawler/firebase_client.py`, `storage_client.py` | 구버전, 미사용 |
| `crawler/test_*.py`, `debug_*.py` (~100개) | 사이트 분석용 일회성 스크립트 (정리 대상) |
| 루트의 `*_dump.json`, `*.html`, `*.png` | 크롤링 분석 중 생긴 덤프 파일 (정리 대상) |
| `SKILLS.md` | 초기 기획 문서. **FastAPI/PostgreSQL은 계획일 뿐 실제 구현은 Firestore 직결** |
| `CATEGORY_MAPPING.md` | 카테고리 매핑 규칙 문서 |
| `README.md` | create-next-app 기본 문서 그대로 |

## 4. 크롤링 대상 9곳

| 사이트 | 방식 | 특이사항 |
|---|---|---|
| 강남맛집 | API POST 페이지네이션 | 8지역 × 7카테고리 루프 (수집량 최대) |
| 리뷰플레이스 | 브라우저 내 `fetch` | Referer 필요 |
| 리뷰노트 | `context.request` API | 재택/배송 제외, 이미지 URL 재조합 |
| 디너의여왕 | DOM + 상세페이지 병렬 | Semaphore(5), 제공내역 정규식 |
| 서울오빠 | DOM + 스크롤 | 배송형/기자단 제외 |
| 놀러와체험단 | 페이지네이션 | `urljoin`으로 이미지 URL 처리 |
| 레뷰 | **로그인** + 응답 인터셉트 | 방문형만, D-day는 API 필드에서 추출 |
| 포블로그 | 무한스크롤 50회 | 키워드로 카테고리 추론 |
| 오마이블로그 | API 2단계 | 카테고리별 app_seq 사전 구축 후 조회 |

**데이터 스키마**: `platform, title, url, region{province,city,normalized}, category(14종), reward{text,value}, meta{type(채널 6종), dday}, image_url, stats{applicants,quota}`
**표준 카테고리 14종**: 음식점·뷰티·여행·숙박·문화·배달·운동·레저·생활·포장·반려동물·식품·유아동·기타
**채널 6종**: 네이버 블로그·인스타 피드·인스타 릴스·유튜브 동영상·유튜브 숏츠·네이버 클립

## 5. 개발 이력 (git 로그 기준, 총 23커밋)

> 모든 커밋이 **2026-02-16 ~ 2026-02-28** 사이에 있고, 그 이후 커밋은 없음. (Feb 28 이후 3월 20일경 파일 변경은 미커밋 리팩터링)

### Phase 0 — 시작 (02-16)
- `8febdac` create-next-app 초기 커밋

### Phase 1 — 크롤러 + 필터 UI 구축 (02-16 ~ 02-28, `171691f`)
- 한 커밋에 107파일: 크롤러 `aggregator.py`(1293줄), region/category mapper, 프론트 3개 컴포넌트, `SKILLS.md`, `CATEGORY_MAPPING.md`, 사이트 분석용 test/debug 스크립트 다수
- 카테고리/지역 필터 고도화, 정렬(최신/마감임박/인기) 추가

### Phase 2 — 자동화 & Firebase (02-28, `103b9b0`)
- GitHub Actions 크롤러 워크플로, Firestore 청크 구조(1000건/chunk), Firebase 설정/인덱스/규칙 추가

### Phase 3 — 모바일 UI·브랜딩 (02-28)
- 놀러와 이미지 URL 버그 수정 + 모바일 반응형 (`0e59fb4`)
- 히어로 영역 정리 여러 차례 (`209d46a`, `9b89ca8`, `2270d36`, `0e584d9`, `b99c14b`)
- SEO/OG 메타, 카카오 공유용 OG 이미지 (`480ec21`, `c08bfae`)
- **서비스명 리뷰어스캐너 → 체험단스캐너** (`1106a17`)
- 필터 터치 영역 확대, 시군구 '전체' 버튼 (`ae8229b`, `b342d6b`)
- 파비콘 추가 (`0b80c98`)

### Phase 4 — 안정화 (02-28)
- Firebase 업로드 버그: batch → 개별 `set()`, 오류 숨김 해결 (`e9a6ea0`)
- Actions에서 서비스 계정 JSON 따옴표 보존 위해 `env` 블록 사용 (`adaed48`)
- 디너의여왕: 스크롤 개선, 놀러와 페이지 제한 제거 (`d6c6ab0`) → 속도 위해 상세 크롤 제거(630건) (`b8c9291`) → 병렬(5) 상세 크롤 복원 (`94f11c5`)
- 레뷰: D-day 필드 추가 및 'N일 남음' 포맷 통일 (`f9ca1a7`, `87a5038`), 로그인 타임아웃 수정 (`b0a72ca`, `a17694a` — "verified working")

### Phase 5 — 미커밋 리팩터링 (3월 20일경 작업, 커밋 안 됨)
- 1348줄짜리 `aggregator.py`를 `crawler/crawlers/` 9개 모듈 + `helpers.py` + 78줄 오케스트레이터로 분리
- 모듈별 독립 브라우저, `Semaphore(5)`로 동시 실행 제한
- 작업트리 기준 파이썬 문법 오류는 없음 (실제 크롤링 실행으로 검증하지는 않음)

## 6. 현재 상태 (2026-11-04 확인)

**확인된 사실**
- 마지막 커밋: 2026-02-28. 이후 8개월 이상 커밋 없음.
- 미커밋: `crawler/aggregator.py`(수정), `crawler/crawlers/`, `crawler/helpers.py`(신규)
- 로컬 `public/campaigns.json`: 14,232건 (강남맛집 5384 · 리뷰노트 4016 · 레뷰 1325 · 서울오빠 1149 · 포블로그 932 · 놀러와 509 · 오마이블로그 415 · 리뷰플레이스 322 · 디너의여왕 180) — 2월 28일 시점 데이터

**알려진 문제 / 위험 (우선순위 순)**
1. 🔴 **Firestore 규칙 만료**: `firestore.rules`가 `2026-03-30`까지만 허용 → 이미 지남. 프론트는 클라이언트 SDK로 읽으므로 **Firestore 읽기가 거부되어 사이트에 데이터가 안 보일 가능성이 높음** (크롤러는 Admin SDK라 규칙의 영향 없음). 수정: 읽기만 공개, 쓰기는 차단
2. 🔴 **레뷰 계정 정보가 코드에 평문 하드코딩** (`crawlers/revu.py`, 이전엔 `aggregator.py`) — 이미 git 이력에 있고 GitHub에 푸시됨. 비밀번호 변경 + GitHub Secrets/환경변수로 이동 필요 (이력 삭제만으로는 부족, 비번 교체가 우선)
3. 🟠 **리팩터링 미커밋**: 컴퓨터 고장 시 유실. 크롤러 실행 검증 후 커밋 필요
4. 🟠 **사이트 구조 변경 가능성**: 8개월 방치 — 9개 크롤러 중 깨진 것이 있을 수 있음. GitHub Actions 최근 실행 결과 확인 필요(60일 비활동 시 scheduled workflow가 자동 비활성화되므로 아마 멈춰 있음)
5. 🟡 `test_*/debug_*` 스크립트 약 100개, 루트 덤프 파일들이 저장소에 커밋되어 있어 지저분함
6. 🟡 `firebase_client.py`, `storage_client.py` 미사용 코드
7. 🟡 `README.md`가 기본 템플릿, `SKILLS.md`는 실제 구현과 불일치(FastAPI/PostgreSQL, 챗봇 검색 등은 미구현)
8. ℹ️ 서비스명이 코드 곳곳(CATEGORY_MAPPING.md 등)에 '리뷰어스캐너'로 남아 있고 UI만 '체험단스캐너'로 변경됨

## 7. 재시작 시 추천 순서

1. **현황 점검**: GitHub Actions 최근 실행·Vercel 배포 상태·Firestore 규칙 확인
2. **보안**: 레뷰 비밀번호 교체 → Secrets로 이동, Firestore 규칙 재작성
3. **리팩터링 검증**: `cd crawler && python aggregator.py` 로 9개 크롤러 개별 동작 확인 후 커밋
4. **크롤러 복구**: 깨진 사이트 수정
5. **정리**: 분석용 스크립트/덤프 파일을 `archive/`로 이동 또는 삭제, README 작성
6. **기능 확장 (선택)**: 마감 지난 캠페인 정리, 검색창(키워드), 챗봇 검색(SKILLS.md 계획), 신규 사이트 추가

## 8. 자주 쓰는 명령

```bash
# 프론트
npm run dev                    # http://localhost:3000

# 크롤러 (로컬)
cd crawler && source ../venv/bin/activate
pip install -r requirements.txt && playwright install chromium
python aggregator.py           # crawler/serviceAccountKey.json 필요 (gitignore됨)
```

---

## 9. 하나씩 살리는 순서 (단계별 체크리스트)

원칙: **"데이터가 사용자에게 보이는 경로"를 끝(프론트)에서부터 앞(크롤러)으로 복구**하고, 각 단계가 끝나면 다음 단계로 넘어간다. 보안 이슈는 서비스를 다시 켜기 전에 처리한다.

### 단계 0. 백업 (5분) — 가장 먼저
- [ ] 미커밋 리팩터링을 별도 브랜치로 보존: `git switch -c refactor/split-crawlers && git add crawler/aggregator.py crawler/crawlers crawler/helpers.py && git commit` (`__pycache__`는 제외)
- 이유: 로컬에만 있는 유일한 작업물. 검증은 뒤에서 하되 유실만 막는다.

### 단계 1. 현황 파악 (읽기만, 수정 없음)
- [ ] GitHub → Actions 탭: 마지막 실행 시각·성공/실패, 워크플로 비활성화 여부 확인 (60일 무활동 시 자동 비활성)
- [ ] Vercel 대시보드: 배포가 살아 있는지, 사이트에 접속하면 캠페인이 보이는지
- [ ] Firebase 콘솔: 프로젝트 `reviewerscanner-dev` 존재 여부, Firestore에 `chunk_N` 문서와 마지막 업데이트 시각(`metrics/status`)
- 결과로 "어디가 죽었는지"가 정해진다: 프론트 / DB 규칙 / 크롤러 / 전부.

### 단계 2. 보안 정리 (서비스 재가동 전 필수)
- [ ] 레뷰 계정 비밀번호 즉시 변경 (코드·git 이력에 노출됨. 이력 삭제보다 **비번 교체가 우선**)
- [ ] `crawlers/revu.py`의 하드코딩 제거 → `os.environ["REVU_EMAIL"]`, `["REVU_PASSWORD"]`
- [ ] GitHub Secrets에 `REVU_EMAIL`, `REVU_PASSWORD` 추가, `crawler.yml`의 `env:`에 전달
- [ ] (선택) 이력에서 비번 제거(`git filter-repo`)는 비번 교체 후 여유 있을 때

### 단계 3. 프론트 데이터 읽기 복구 (사이트가 보이게)
- [ ] `firestore.rules` 교체 — 읽기만 공개, 쓰기 차단 (Admin SDK는 규칙을 우회하므로 크롤러에 영향 없음):
  ```
  match /{document=**} { allow read: if true; allow write: if false; }
  ```
- [ ] 배포: `firebase deploy --only firestore:rules`
- [ ] `npm run dev`로 로컬에서 캠페인이 뜨는지 확인 → 이 시점의 데이터는 **2월 데이터(낡음)** 일 수 있음
- 이 단계에서 "사이트는 살아났지만 데이터가 오래됨" 상태가 된다.

### 단계 4. 크롤러 1개씩 로컬 검증 (리팩터링 검증 겸용)
전체를 한 번에 돌리지 말고 사이트별로 하나씩 실행해 결과 건수를 본다 (`run()`이 리스트 반환):
```bash
cd crawler && source ../venv/bin/activate
python -c "import asyncio; from crawlers import kangnam; r=asyncio.run(kangnam.run()); print(len(r), r[:1])"
```
권장 순서 (안정적·수집량 큰 것 → 까다로운 것):
1. 강남맛집 (API) → 2. 리뷰노트 (API) → 3. 리뷰플레이스 (API) → 4. 오마이블로그 (API)
5. 놀러와체험단 → 6. 서울오빠 → 7. 포블로그 → 8. 디너의여왕 (상세 병렬)
9. **레뷰 (로그인, 가장 깨지기 쉬움 — 마지막)**

판정 기준: 2월 기준 건수(§6 표)와 크게 차이 나면 사이트 구조 변경 의심 → 해당 크롤러만 수정. 한 개가 실패해도 `run_with_sem`이 빈 리스트로 처리하므로 나머지는 계속 동작한다.

### 단계 5. 전체 실행 & 업로드
- [ ] `python aggregator.py` 전체 실행 (로컬 `serviceAccountKey.json` 필요) → `public/campaigns.json` 건수, Firestore 청크 업로드 로그 확인
- [ ] 로컬 프론트에서 최신 데이터·필터·정렬 정상 확인
- [ ] 정상이면 리팩터링 브랜치를 `main`에 머지

### 단계 6. 자동화 재가동
- [ ] GitHub Actions 워크플로 Enable → `workflow_dispatch`로 수동 1회 실행해 성공 확인
- [ ] 이후 cron 정상 동작 확인. (저장소가 60일 이상 조용하면 또 꺼지므로, 주기적 커밋이 없는 대신 가끔 확인 필요)
- [ ] 소요 시간·메모리 확인 (동시 5개 Chromium, Actions 7GB 한계)

### 단계 7. 정리 (서비스가 돌아간 뒤)
- [ ] `test_*`, `debug_*`, 루트 덤프(`*_dump.json`, `*.html`, `*.png`)를 `archive/`로 이동 또는 삭제
- [ ] 미사용 `firebase_client.py`, `storage_client.py` 삭제
- [ ] `README.md` 작성 (실행법, 구조, 환경변수), `SKILLS.md`를 실제 구현에 맞게 수정
- [ ] '리뷰어스캐너' 잔존 표기를 '체험단스캐너'로 통일

### 단계 8. 기능 확장 (선택, 위 단계가 모두 끝난 후)
- 마감된 캠페인 자동 제거 / 중복 제거
- 키워드 검색창, 챗봇 자연어 검색(SKILLS.md 계획)
- 신규 체험단 사이트 추가 (현재 9곳 → 계획은 20곳)
- 프로덕션용 Firebase 프로젝트 분리 (현재 `-dev` 하나)

### 단계별 소요 감각
| 단계 | 목표 상태 | 예상 |
|---|---|---|
| 0~1 | 백업 완료, 죽은 곳 파악 | 30분 |
| 2~3 | 보안 해결 + 사이트에 (낡은) 데이터 표시 | 1~2시간 |
| 4~5 | 9개 크롤러 검증/수리 + 최신 데이터 | 반나절~며칠 (사이트 변경량에 좌우) |
| 6 | 매시간 자동 갱신 복귀 | 1시간 |
| 7~8 | 정리·확장 | 자유 |

---

## 10. 크롤러 개별 테스트 결과 (2026-11-05, 로컬 `run()` 단독 실행)

| 사이트 | 결과 | 비고 |
|---|---|---|
| 강남맛집 | ✅ 4,270 | |
| 서울오빠 | ✅ 1,151 | |
| 레뷰 | ✅ 892 | 로그인 성공. 2월(1,325)보다 감소 — 원인 미확인 |
| 놀러와체험단 | ✅ 440 | |
| 오마이블로그 | ✅ 344 | |
| 리뷰플레이스 | ✅ 304 | |
| 리뷰노트 | ✅ 12,122 (수정) | 직접 API 호출이 403 → `page.evaluate(fetch)`로 변경. 4,000건 상한 제거, `has_more=False`까지 수집(전체 12,793건 중 배송/재택 등 제외). 전부 마감일이 미래인 모집중 캠페인 확인 |
| 포블로그 | ✅ 717 (수정) | 목록 URL이 301로 변경됨 → 새 URL + `domcontentloaded`. 채널/카테고리가 '기타'로 많이 잡히는지 추가 확인 필요 |
| 디너의여왕 | ✅ 8,869 (재작성) | 스크롤 대신 `POST /taste/taste_list?page=N`(30건/페이지, `has_next`로 종료) 사용. 제공내역은 카드 서브텍스트에서 바로 파싱(상세 요청은 서버가 초당 ~1.5건으로 제한해 불가). D-day/신청수 파싱 버그도 수정. 59초 |

수정 파일(미커밋): `crawlers/reviewnote.py`, `crawlers/fourblog.py`, `crawlers/dinnerqueen.py`
미검증: 전체 `aggregator.py` 통합 실행, Firestore 업로드.

**수집량 변화 (2월 → 11월)**: 리뷰노트 4,016→12,122, 디너의여왕 180→8,869. 2월에는 코드 상한/스크롤 한계로 실제보다 적게 수집했던 것. 전체는 약 29,000건으로 이전(14,232)의 2배.
**후속 확인 필요**: Firestore 청크 문서 크기(1000건/청크, 문서 1MB 한도), 프론트 SSR이 청크 30개 가량을 한 번에 읽는 성능, `normalize_reward`가 "10개" 같은 비금액 숫자를 보상금액으로 해석하는 문제.

---

## 11. 정적 사이트 + Cloudflare R2 전환 (2026-11-05, 코드 작업 완료 / 배포 전)

**구조**: GitHub Actions 크롤러 → `v1/campaigns.json.gz`를 R2 버킷(`reviewerscanner-data`)에 업로드 → Cloudflare Pages Function(`/api/campaigns`)이 R2에서 읽어 응답 → 정적 사이트의 브라우저가 받아 필터링.

| 변경 | 파일 |
|---|---|
| 정적 export + 이미지 최적화 해제 | `next.config.ts` |
| Firebase 제거, 브라우저에서 JSON fetch + 로딩/오류 UI | `app/page.tsx`, `app/components/CampaignList.tsx`, `app/lib/firebase.ts` 삭제, `firebase` 패키지 제거 |
| R2 읽기 함수 (바인딩 이름 `DATA_BUCKET`) | `functions/api/campaigns.js` |
| R2 업로더 (gzip, boto3) + 최소 5,000건 미만이면 업로드 중단 | `crawler/r2_client.py`, `crawler/aggregator.py` |
| Firebase 단계 제거, R2 Secrets 전달 | `.github/workflows/crawler.yml`, `crawler/requirements.txt` |

**검증**: `next build` 통과. R2 함수를 흉내 낸 로컬 서버로 14,232건 로드·검색(동탄 108건) 정상, 콘솔 오류 없음. 업로더는 가짜 boto3로 호출 인자·한글 왕복 확인. **실제 R2 업로드와 Cloudflare Pages 배포는 미검증.**

**배포 시 남은 작업**: Pages 프로젝트 생성(빌드 `npm run build`, 출력 `out`) → R2 바인딩 `DATA_BUCKET` 추가 → `scan.reviewerscanner.com` 등록 → 호스팅KR CNAME 변경 → main에 반영 후 Actions 수동 실행.

---

## 12. 강남맛집: 한국 IP 기기에서 수집 (2026-11-05)

**원인(확정)**: 강남맛집은 GitHub Actions(미국 IP)에서 연결 자체가 맺어지지 않음(`curl connect=0`, 20개 해외 점검 서버도 전부 실패, 한국 가정용 IP는 정상). 브라우저 문제가 아니라 IP 문제. 같은 서버에서 리뷰플레이스·구글은 정상.

**구조**
```
[한국 IP Mac] run_kangnam.py (1시간마다, launchd) → R2 v1/parts/kangnam.json.gz
[GitHub Actions] 나머지 8곳 수집 + 부분 파일 병합(36시간 이내만) → R2 v1/campaigns.json.gz
```
- `crawlers/kangnam.py`: Playwright 제거, requests만 사용(4,814건 / 9~27초)
- `r2_client.py`: `upload_part` / `load_part` (신선도 36시간, 수집 후 지난 날짜만큼 `N일 남음` 보정, 마감 지난 항목 제외)
- `helpers.shift_dday`, `crawler/run_kangnam.py`, `scripts/mac/install_kangnam_job.sh` (등록) / `uninstall_kangnam_job.sh` (제거)
- Mac 작업은 `~/.reviewerscanner/`에 복사해서 실행(`~/Documents`는 launchd가 접근 못 할 수 있음). 코드 수정 후에는 install 스크립트 재실행
- R2 토큰은 `~/.config/reviewerscanner/r2.env`(권한 600)에만 저장. GitHub Secrets와 별도의 **버킷 범위 토큰** 사용 권장

**한계**: Mac이 꺼져 있거나 VPN(해외 IP)이면 갱신 안 됨 → 36시간 뒤 사이트에서 강남맛집 제외. 하루 1회 자동 깨우기: `sudo pmset repeat wakeorpoweron MTWRFSU 07:55:00`
**미검증**: 실제 launchd 등록·실행, 실제 R2 업로드/병합, 포블로그 원인(진단 로그 대기).
