"""
설정 파일.
민감정보(토큰/API키)는 코드에 넣지 말고 환경변수로 주입한다.
- 로컬 실행: .env 파일 또는 export
- GitHub Actions: 저장소 Settings > Secrets and variables > Actions 에 등록
"""
import os


def _load_dotenv() -> None:
    """같은 폴더의 .env 파일을 환경변수로 로드 (이미 설정된 값은 유지)."""
    path = os.path.join(os.path.dirname(__file__), ".env")
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key, value = key.strip(), value.strip().strip("'\"")
            os.environ.setdefault(key, value)


_load_dotenv()


# ── 텔레그램 ─────────────────────────────────────────────
# @BotFather 로 봇을 만들면 받는 토큰
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
# 내 채팅 ID (아래 README 참고). 여러 명에게 보내려면 콤마로 구분
TELEGRAM_CHAT_IDS = [
    c.strip() for c in os.environ.get("TELEGRAM_CHAT_IDS", "").split(",") if c.strip()
]

# ── 공공데이터포털(data.go.kr) 서비스키 ──────────────────
# '인사혁신처_공공기관 채용정보' API 활용신청 후 받는 "일반 인증키(Decoding)"
# → 공공기관/공기업(alio) 수집에 사용
DATA_GO_KR_SERVICE_KEY = os.environ.get("DATA_GO_KR_SERVICE_KEY", "")

# ── 사람인 공식 API ─────────────────────────────────────
# https://oapi.saramin.co.kr 이용신청 후 발급받는 access-key
SARAMIN_ACCESS_KEY = os.environ.get("SARAMIN_ACCESS_KEY", "")

# ── 원티드 공식 OpenAPI ─────────────────────────────────
# https://openapi.wanted.jobs 인증키 신청 후 메일로 발급받는 key
WANTED_API_KEY = os.environ.get("WANTED_API_KEY", "")

# ── 수집 대상 on/off ────────────────────────────────────
ENABLE_WORKNET = os.environ.get("ENABLE_WORKNET", "1") == "1"   # 민간기업(워크넷)
ENABLE_ALIO = os.environ.get("ENABLE_ALIO", "1") == "1"         # 공공기관/공기업
ENABLE_GOSI = os.environ.get("ENABLE_GOSI", "1") == "1"         # 공무원 전산직
ENABLE_SARAMIN = os.environ.get("ENABLE_SARAMIN", "1") == "1"   # 사람인(공식 API)
ENABLE_WANTED = os.environ.get("ENABLE_WANTED", "1") == "1"     # 원티드(공식 API)

# ── 수집 트랙 on/off ────────────────────────────────────
# 개발자 공고 트랙 (기존 동작)
ENABLE_DEV_TRACK = os.environ.get("ENABLE_DEV_TRACK", "1") == "1"
# 교통 분야 공고 트랙 (공기업·공무원 + 민간, 교통기사 자격증 우대 공고 우선)
ENABLE_TRANSPORT_TRACK = os.environ.get("ENABLE_TRANSPORT_TRACK", "1") == "1"

# ── 필터 조건 ───────────────────────────────────────────
# 개발자 공고로 판단할 키워드 (제목/직무에 하나라도 있으면 통과)
DEV_KEYWORDS = [
    # 한글
    "개발", "백엔드", "프론트", "풀스택", "서버", "웹개발", "앱개발",
    "소프트웨어", "전산", "정보처리", "정보보호", "데이터", "플랫폼",
    "시스템개발", "응용", "SW", "S/W",
    # 영문
    "developer", "engineer", "backend", "back-end", "frontend", "front-end",
    "fullstack", "full-stack", "software", "server",
    # 스택
    "java", "spring", "python", "django", "fastapi", "node", "react",
    "vue", "kotlin", "golang", "nest",
]

# ── 민간기업 공고 스택 필터 ─────────────────────────────
# 민간 소스(워크넷/사람인/원티드)는 아래 스택 키워드가 있는 공고만 받는다.
# 공공기관/공무원 공고는 스택 표기가 없는 경우가 많아 적용하지 않는다.
PRIVATE_SOURCES = {"worknet", "saramin", "wanted"}
STACK_KEYWORDS = [
    "fastapi", "django", "flask", "python", "파이썬", "장고",
    "react", "리액트", "next.js", "nextjs",
]

# 제외 키워드 (있으면 거른다) — 오탐 줄이기용
EXCLUDE_KEYWORDS = [
    "영업", "회계", "경리", "간호", "요양", "운전", "생산직", "조리",
    "청소", "경비", "미화",
]

# ── 교통 트랙 키워드 ────────────────────────────────────
# 교통 분야 공고로 판단할 키워드. 개발 공고와 달리 민간에도 스택 필터를
# 적용하지 않는다 (교통 직무는 파이썬/리액트를 요구하지 않는 게 정상).
TRANSPORT_KEYWORDS = [
    # 교통 일반·계획·정책
    "교통", "교통계획", "교통공학", "교통정책", "교통행정", "교통기술",
    "교통안전", "교통영향평가", "교통영향", "교통수요", "교통량", "교통조사",
    "교통운영", "교통시설", "교통체계", "교통정보",
    # 신호·ITS·모빌리티
    "교통신호", "신호운영", "ITS", "C-ITS", "지능형교통", "지능형 교통",
    "모빌리티", "스마트모빌리티", "자율주행", "UAM", "수요응답",
    # 도로·철도·대중교통
    "도로", "고속도로", "철도", "도시철도", "광역철도", "궤도", "선로",
    "대중교통", "버스노선", "노선체계", "환승", "간선급행",
    # 인접 분야 (교통 직무가 함께 붙는 경우가 많음)
    "도시계획", "국토계획", "주차", "보행", "자전거",
    # 영문
    "transportation", "traffic", "transit", "mobility", "railway",
]

# ⭐ 우대 자격증 (국가기술자격 교통기사 계열) — 이게 걸리면 최우선 발송
TRANSPORT_CERT_KEYWORDS = [
    "교통기사", "교통산업기사", "교통기술사",
    "engineer transportation",
]

# 관련 자격증 — 발송 메시지에 함께 표시하지만 ⭐는 붙이지 않는다
TRANSPORT_CERT_RELATED = [
    "교통안전관리자", "도시계획기사", "도시계획기술사",
    "철도교통관제사", "철도차량기사", "토목기사", "토목기술사",
]

# 오탐 유발 문구 — 교통 키워드 판정 '전에' 본문에서 지워버린다.
# ("교통비 지원", "역세권" 같은 복지 문구 때문에 무관한 공고가 딸려오는 것 방지)
TRANSPORT_NOISE_PHRASES = [
    "교통비", "교통 비", "교통편", "교통 편", "교통편리", "교통 편리",
    "교통 좋", "교통이 좋", "대중교통 이용", "역세권", "셔틀버스", "셔틀 버스",
    "통근버스", "통근 버스", "주차가능", "주차 가능", "주차장 완비", "주차비",
]

# 교통 트랙에서 제외할 직무 — 운전·배송직 (자격증 우대 공고면 예외로 살림)
TRANSPORT_EXCLUDE_KEYWORDS = [
    "운전원", "운전기사", "버스기사", "택시기사", "화물기사", "지게차",
    "배송", "배달", "택배", "대리운전", "수송원",
    "운행승무원", "신호수", "순찰요원",
]

# 워크넷·사람인에 던질 교통 분야 검색어
TRANSPORT_SEARCH_KEYWORDS = [
    "교통기사", "교통계획", "교통공학", "교통안전", "교통영향평가",
    "교통신호", "ITS", "교통정책",
]

# 공무원 공고에서 교통 계열로 볼 직렬 키워드
GOSI_TRANSPORT_KEYS = [
    "교통", "도로", "철도", "시설", "토목", "도시계획",
]

# 경력직 위주로 보고 싶을 때 True (신입만 있는 공고 일부 제외).
# 공공/공무원은 경력 구분이 애매해서 무시하고 다 통과시킴.
EXPERIENCED_ONLY = os.environ.get("EXPERIENCED_ONLY", "0") == "1"

# 한 번에 보낼 최대 공고 수 (너무 많으면 잘라냄)
MAX_ITEMS_PER_RUN = int(os.environ.get("MAX_ITEMS_PER_RUN", "40"))

# 이미 보낸 공고 기록 파일
SEEN_PATH = os.path.join(os.path.dirname(__file__), "data", "seen.json")
