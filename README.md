# 채용공고 알림봇 (텔레그램)

매일 아침 8시(KST), 채용공고를 텔레그램으로 받아보는 봇.
서버 없이 **GitHub Actions**로 무료 자동 실행된다.

## 두 개의 트랙

| 트랙 | 대상 | 비고 |
|---|---|---|
| 💻 개발자 | 공기업·공무원 전산직 + 민간 개발자 | 민간은 관심 스택(FastAPI/Django/Python/React) 공고만 |
| 🚦 교통 분야 | 공기업·공무원 교통직 + 민간 교통 엔지니어링 | **교통기사 계열 자격증 우대 공고는 ⭐ 로 최우선 발송** |

교통 트랙은 자격증 우대 공고(⭐)를 먼저 정렬하므로, `MAX_ITEMS_PER_RUN`
상한에 걸려 잘려나가는 일이 없다. 두 트랙은 `ENABLE_DEV_TRACK` /
`ENABLE_TRANSPORT_TRACK` 으로 따로 끌 수 있다.

## 수집 소스

| 소스 | 대상 | 방식 |
|---|---|---|
| 원티드 OpenAPI | 민간 기업 | 공식 API (Jobs + Companies) |
| 사람인 API | 민간 기업 | 공식 API (하루 500회) |
| 워크넷(고용24) 채용정보 | 민간 기업 | 검색결과 수집 (하루 1회, robots.txt 허용) |
| 공공기관 채용정보 API | 공기업·공공기관 | 공공데이터포털 공식 API (최대 5페이지) |
| 국가공무원채용시스템 | 공무원 전산·교통직 | 공고 게시판 스크래핑 (접수중인 공고만) |

> **잡코리아는 제외했다.** 개인용 공식 API가 없고, 크롤링은 약관 위반 +
> 국내 판례(잡코리아 vs 사람인) 리스크가 있다. 위 4개 소스로 국내 개발자
> 채용 대부분이 커버되므로 잡코리아 하나 때문에 약관 위반을 감수할 실익이 적다.
> 원티드·사람인은 **크롤링이 아니라 공식 API**로 붙였다(약관 문제 없음).

## 동작

`수집 → 트랙 분류(개발/교통) → 중복 제거 → ⭐ 우선 정렬 → 텔레그램 발송 → 발송기록 저장(seen.json)`

같은 공고를 두 번 보내지 않도록 `data/seen.json`에 기록하고, GitHub Actions가
매 실행 후 이 파일을 커밋해 상태를 유지한다.

---

## 설정 (10분)

### 1. 텔레그램 봇 만들기
1. 텔레그램에서 **@BotFather** 검색 → `/newbot` → 이름 지정 → **봇 토큰** 받기
2. 만든 봇과 대화창을 열고 아무 메시지나 하나 보낸다
3. 브라우저에서 아래 주소 열기 (`<토큰>` 자리에 봇 토큰):
   `https://api.telegram.org/bot<토큰>/getUpdates`
4. 응답 JSON에서 `"chat":{"id": 숫자}` → 이 **숫자가 chat_id**

### 2. 공공데이터포털 API 키 발급 (공공기관 공고용)
1. [data.go.kr](https://www.data.go.kr) 회원가입
2. [인사혁신처_공공기관 채용정보](https://www.data.go.kr/data/15125273/openapi.do)에서 **활용신청** (즉시 승인, 무료)
3. 마이페이지 → **일반 인증키(Decoding)** 복사 → `DATA_GO_KR_SERVICE_KEY`

> **워크넷(고용24) 민간기업 공고는 키 없이 동작한다.** 오픈API 인증키가
> 개인에게 발급되지 않아 채용정보 검색 결과를 하루 1회 읽는 방식
> (robots.txt 허용 경로, 정부 공공 사이트의 공개 정보, 비상업적 개인 용도).
> 검색 키워드는 `collectors/worknet.py`의 `SEARCH_KEYWORDS`에서 조정.

### 3. 사람인 API 키 발급 (선택)
1. [oapi.saramin.co.kr](https://oapi.saramin.co.kr) 이용신청 → 승인 후 **access-key** 발급
2. 하루 500회 호출 가능. 검색어는 `collectors/saramin.py`의 `DEFAULT_KEYWORDS`에서 조정
3. 키가 없으면 사람인 소스는 자동으로 건너뛴다

### 4. 원티드 API 키 발급 (선택)
1. [openapi.wanted.jobs/apply](https://openapi.wanted.jobs/apply/) 에서 Key 발급 신청
2. 접수 후 **3영업일 이내 메일**로 인증키 수신
3. 발급되면 [api-docs/v1](https://openapi.wanted.jobs/api-docs/v1/) 문서를 보고
   `collectors/wanted.py`의 `BASE_URL`·인증 헤더·응답 필드명(TODO)을 맞춘다
4. 키가 없으면 원티드 소스는 자동으로 건너뛴다

### 5. GitHub에 올리고 Secrets 등록
1. 이 폴더를 본인 GitHub 저장소(private 권장)에 push
2. 저장소 **Settings → Secrets and variables → Actions → New repository secret** 에 등록:

| 이름 | 값 | 필수 |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | 봇 토큰 | ✅ |
| `TELEGRAM_CHAT_IDS` | chat_id (여러 명이면 `123,456`) | ✅ |
| `DATA_GO_KR_SERVICE_KEY` | 일반 인증키(Decoding) | 공공기관용 |
| `SARAMIN_ACCESS_KEY` | 사람인 access-key | 선택 |
| `WANTED_API_KEY` | 원티드 인증키 | 선택 |

> 키를 넣은 소스만 동작한다. 일단 텔레그램 + 공공데이터 키만으로 시작하고,
> 사람인·원티드는 나중에 붙여도 된다.

3. **Actions** 탭 → 워크플로우 선택 → **Run workflow**로 즉시 테스트
4. 이후 매일 아침 8시(KST) 자동 실행

---

## 로컬 테스트

```bash
pip install -r requirements.txt

export TELEGRAM_BOT_TOKEN="..."
export TELEGRAM_CHAT_IDS="123456789"
export DATA_GO_KR_SERVICE_KEY="..."

python main.py
```

## 커스터마이징 (`config.py`)

### 공통
- `ENABLE_WORKNET / ENABLE_ALIO / ENABLE_GOSI / ENABLE_SARAMIN / ENABLE_WANTED`: 소스별 on/off
- `ENABLE_DEV_TRACK / ENABLE_TRANSPORT_TRACK`: 트랙별 on/off
- `MAX_ITEMS_PER_RUN`: 1회 최대 발송 건수 (상한 초과분은 다음 실행으로 넘어감)
- 발송 시각 변경: `.github/workflows/daily.yml`의 `cron` (UTC 기준. KST−9시간)

### 개발자 트랙
- `DEV_KEYWORDS` / `EXCLUDE_KEYWORDS`: 공고 필터 키워드
- `STACK_KEYWORDS`: 민간 공고에 요구하는 스택 (여기에 없으면 민간 개발 공고는 탈락)
- `EXPERIENCED_ONLY=1`: 경력직 위주 (민간 공고에서 '신입 전용' 일부 제외)

### 교통 트랙
- `TRANSPORT_KEYWORDS`: 교통 분야 판정 키워드 (교통계획·ITS·철도·도로 등)
- `TRANSPORT_CERT_KEYWORDS`: ⭐ 를 붙일 자격증 (교통기사 계열)
- `TRANSPORT_CERT_RELATED`: 함께 표시만 하는 관련 자격증 (도시계획기사 등)
- `TRANSPORT_NOISE_PHRASES`: **오탐 차단용.** '교통비 지원'·'역세권' 같은 복지
  문구를 판정 전에 지운다. 이게 없으면 무관한 공고가 대량으로 딸려온다
- `TRANSPORT_EXCLUDE_KEYWORDS`: 운전·배송직 제외 (단 ⭐ 자격증 우대면 살림)
- `TRANSPORT_SEARCH_KEYWORDS`: 워크넷·사람인에 던지는 검색어
- `GOSI_TRANSPORT_KEYS`: 공무원 공고에서 교통 계열로 볼 직렬 키워드

### 교통 트랙 필터가 신경 쓰는 것

라이브 실행에서 실제로 터졌던 오탐들이라 함부로 단순화하면 안 된다:

1. **복지 문구** — "교통비 지원", "역세권", "셔틀버스"는 판정 전에 지운다.
2. **검색어 오염** — 수집기가 `extra["검색어"]`에 질의어를 남기는데, 이걸
   공고 내용으로 취급하면 "교통기사"로 검색한 결과 **전부**가 자격증 우대
   공고로 오인된다. 교통 판정·자격증 판정에서는 이 키를 제외한다.
3. **영문 약어** — `ITS` 를 소문자로 비교하면 영어 문장의 "its"에 걸린다.
   전부 대문자인 키워드는 대소문자를 구분해 단어 경계로 매칭한다.
   (`transit` 이 `transition` 에 걸리는 것도 같은 이유로 단어 경계 매칭)
4. **회사명** — 공공기관은 기관명 자체가 지표(한국교통안전공단)라 근거로
   쓰지만, 민간은 사명이 우연히 겹치는 경우(위밋모빌리티, 한국교통대학교)가
   많아 회사명을 근거에서 뺀다.

## 테스트

```bash
PYTHONPATH=. python tests/test_filters.py
```

필터 오탐 케이스 23개를 확인한다. 키워드를 손볼 때 여기부터 돌려볼 것.

## 알아둘 점

- **정확도**: 두 공식 API는 엔드포인트/필드명이 명세서마다 조금씩 다르다.
  첫 실행에서 0건이 나오면 명세서의 `요청주소`·파라미터명·응답 필드명을
  `collectors/`의 해당 파일과 맞춰야 한다 (코드에 `TODO`로 표시해둠).
- **공무원 소스**: 정부 사이트 개편이 잦다. 게시판 HTML 구조가 바뀌면
  `collectors/gosi.py`의 URL/셀렉터를 조정한다.
- **GitHub Actions 스케줄**: 무료 러너 부하에 따라 예약 실행이 수 분~수십 분
  지연될 수 있다(정상). 정확한 시각이 중요하면 개인 서버 cron을 고려.
