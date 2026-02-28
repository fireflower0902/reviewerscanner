# SKILLS.md

## 1. 프로젝트 개요 (Project Overview)
**프로젝트명**: 블로그 체험단 애그리게이터 (Blog Experience Group Aggregator)

**목표**: 20여 개 체험단 사이트의 데이터를 크롤링 및 정규화하여, 스카이스캐너(Skyscanner) 수준의 직관적인 필터링과 깔끔한 UI를 제공하는 통합 플랫폼 구축.

**핵심 가치**:
- **데이터 무결성**: 타 서비스의 고질적인 문제인 지역 누락(예: 화성시 검색 시 동탄 미노출) 해결.
- **사용자 경험(UX)**: 모바일/데스크탑 환경에 최적화된 반응형 필터링 및 자연어 챗봇 검색 지원.

**사용 도구**: Anti-Gravity (Agent), MCP (NotebookLM, Stitch).

## 2. 기술 스택 및 표준 (Tech Stack & Standards)
- **언어**: Python 3.10+ (크롤링/백엔드), TypeScript (프론트엔드).
- **프레임워크**: FastAPI (REST API), Next.js 14+ (App Router).
- **데이터베이스**: PostgreSQL (관계형 데이터, 필터링 쿼리 최적화).
- **크롤링**: Playwright (동적 페이지), BeautifulSoup4 (정적 페이지).
- **스타일링**: Tailwind CSS, Shadcn/UI (디자인 시스템).

## 3. 핵심 역량 및 AI 활용 규칙 (Core Competencies)
### Skill 1: 고급 크롤링 및 안정성 (Advanced Web Scraping)
- **동적 페이지 처리**: 대부분의 대상 사이트가 JavaScript로 렌더링되므로, 단순 requests 대신 **Playwright**를 사용하여 실제 브라우저 환경처럼 데이터를 수집한다.
- **선택자(Selector) 관리**: HTML 구조 변경에 대비해 CSS 선택자를 하드코딩하지 않는다.
- **Action**: 크롤링 실패 시, NotebookLM을 통해 최신 DOM 구조 정보를 조회하도록 MCP에 요청한다.
- **봇 탐지 우회**: User-Agent 랜덤화, 요청 간 지연 시간(Random Delay) 적용, IP 차단 방지 로직을 포함한다.

### Skill 2: 데이터 정규화 (Data Normalization) - 필터링의 핵심
**목표**: 20개 사이트의 파편화된 데이터를 하나의 통일된 스키마로 변환한다.

- **지역 표준화 (Geo-Tagging Rule)**:
  - **문제**: "동탄", "병점", "봉담" 등으로만 표기된 데이터는 "화성시" 검색 시 누락됨.
  - **해결**: 세부 지역명이 감지되면 상위 행정구역인 **"화성시(Region Depth 2)"**를 자동으로 매핑하여 저장한다. (Mapping Table 필수 적용)
- **보상 가치 수치화**:
  - **텍스트**: "3만원 식사권", "50,000 포인트" -> **변환**: `reward_value: 30000` (Integer)
  - **목적**: "3만 원 이상"과 같은 가격 슬라이더(Slider) 필터링 기능을 위함.
- **날짜 통일**: 상대 날짜("D-3")를 절대 날짜(YYYY-MM-DD)로 변환하여 "마감 임박순" 정렬을 지원한다.

### Skill 3: 하이브리드 검색 아키텍처 (Hybrid Search Architecture)
- **통합 API 설계**: UI 필터링과 챗봇이 동일한 백엔드 로직을 사용해야 한다.
  - **엔드포인트 예시**: `GET /api/campaigns?region=hwaseong&min_price=30000&category=food`
- **우선순위**:
  - **UI 필터링 (Main)**: 사용자가 직접 클릭하여 검색 (가장 빈번한 사용 패턴).
  - **AI 챗봇 (Sub)**: 자연어로 복잡한 조건을 검색 (보조 기능).

### Skill 4: AI 챗봇 및 자연어 처리 (AI Chatbot & NLP)
- **기능**: 사용자의 자연어 입력을 SQL 또는 API 쿼리 파라미터로 변환.
- **의도 파악 예시**:
  - **유저 입력**: "화성시 3만원대 고깃집 찾아줘"
  - **변환 로직**:
    - Location: "화성시" -> `region_code='HS'`
    - Price: "3만원대" -> `reward_value >= 30000`
    - Keyword: "고깃집" -> `category='food' AND title LIKE '%고기%'`

### Skill 5: 글로벌 애그리게이터급 UI/UX 표준 (High-End UX Standard)
**목표**: 스카이스캐너(Skyscanner), 호텔스컴바인과 동등한 사용성을 제공한다.

#### 5.1. 반응형 레이아웃 전략 (Responsive Layout)
- **데스크탑 (Desktop)**:
  - **Sticky Sidebar**: 필터 패널(지역, 가격 등)을 좌측에 고정하여, 스크롤을 내려도 언제든 조건을 변경할 수 있게 한다.
- **모바일 (Mobile)**:
  - **Bottom Sheet**: 좁은 화면에 필터를 늘어놓지 않고, '필터' 버튼 클릭 시 하단에서 올라오는 서랍(Drawer) 형태를 사용한다.
  - **Sticky CTA**: 주요 버튼이나 요약 정보는 화면 하단에 고정한다.

#### 5.2. 필터링 컴포넌트 디테일 (Smart Components)
- **즉시 반응 (Instant Feedback)**: 필터 조작 시 별도의 '적용' 버튼 없이 리스트가 실시간으로 갱신되어야 한다 (React Query 활용).
- **이중 슬라이더 (Dual Range Slider)**: 가격대 설정 시 '최소~최대' 범위를 직관적으로 조절할 수 있게 한다.
- **칩(Chips) UI**: 카테고리 선택 시 직관적인 타원형 버튼(Chip)을 사용하여 다중 선택을 돕는다.

#### 5.3. 시각적 계층 구조 (Visual Hierarchy)
- **카드 디자인**:
  - **썸네일**: 4:3 비율, 둥근 모서리.
  - **강조점**: **제공 가치(예: 50,000원)**는 브랜드 컬러와 굵은 폰트로 가장 눈에 띄게 배치한다.
  - **마감일**: "D-Day" 뱃지를 사용하여 긴급성을 시각적으로 알린다.
- **로딩**: 스피너 대신 스켈레톤(Skeleton) UI를 사용하여 데이터 로딩 중 체감 대기 시간을 줄인다.

## 4. 코딩 행동 지침 (Coding Behavior Guidelines)
- **모듈화 (Modularity)**: Crawler, Normalizer, API, UI Component를 철저히 분리하여 유지보수성을 높인다.
- **TDD (테스트 주도 개발)**: 특히 Skill 2(정규화) 로직은 "화성시 매핑"이 제대로 되는지 확인하는 단위 테스트(Unit Test)를 통과한 후 구현한다.
- **에러 핸들링**: 특정 사이트의 크롤링 실패가 전체 시스템 다운으로 이어지지 않도록 try-except 블록을 개별 사이트 단위로 적용한다.
- **디자인 시스템 준수**: 버튼 크기, 폰트 사이즈, 색상 코드를 변수화하여 일관된 디자인을 유지한다.
