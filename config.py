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

# ── 고용24(work24.go.kr) 오픈API 인증키 ─────────────────
# 워크넷 민간기업 채용정보용. 고용24 오픈API에서 별도 신청 (data.go.kr 키와 다름!)
WORK24_AUTH_KEY = os.environ.get("WORK24_AUTH_KEY", "")

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

# 제외 키워드 (있으면 거른다) — 오탐 줄이기용
EXCLUDE_KEYWORDS = [
    "영업", "회계", "경리", "간호", "요양", "운전", "생산직", "조리",
    "청소", "경비", "미화",
]

# 경력직 위주로 보고 싶을 때 True (신입만 있는 공고 일부 제외).
# 공공/공무원은 경력 구분이 애매해서 무시하고 다 통과시킴.
EXPERIENCED_ONLY = os.environ.get("EXPERIENCED_ONLY", "0") == "1"

# 한 번에 보낼 최대 공고 수 (너무 많으면 잘라냄)
MAX_ITEMS_PER_RUN = int(os.environ.get("MAX_ITEMS_PER_RUN", "40"))

# 이미 보낸 공고 기록 파일
SEEN_PATH = os.path.join(os.path.dirname(__file__), "data", "seen.json")
