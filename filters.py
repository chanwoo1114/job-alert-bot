"""공고를 개발자 트랙 / 교통 트랙으로 분류하는 필터."""
import re

import config
from collectors import Job

# 수집기가 '어떤 검색어로 찾았는지' 기록해두는 extra 키.
# 이건 공고 내용이 아니라 우리가 던진 질의어이므로, 교통 트랙 판정과
# 자격증 판정에서는 근거로 쓰지 않는다.
# (안 걸러내면 "교통기사"로 검색한 결과 전부가 자격증 우대 공고로 오인된다)
QUERY_EXTRA_KEYS = {"검색어"}


def _text(job: Job, skip_extra_keys: set = frozenset(),
           with_company: bool = True) -> str:
    extra = " ".join(
        str(v) for k, v in job.extra.items() if k not in skip_extra_keys
    )
    parts = [job.title, job.category, extra]
    if with_company:
        parts.insert(2, job.company)
    return " ".join(parts)


def _kind(kw: str) -> str:
    """키워드 매칭 방식 결정.

    - hangul : 한글 → 부분 문자열 (한국어는 띄어쓰기가 일정하지 않다)
    - acronym: 전부 대문자인 영문 약어 → 대소문자 구분 + 단어 경계
               ("ITS"를 소문자로 비교하면 영어 문장의 "its"에 걸린다)
    - word   : 그 외 영문 → 대소문자 무시 + 단어 경계
               (부분 문자열이면 "transit"이 "transition"에 걸린다)
    """
    if re.search(r"[가-힣]", kw):
        return "hangul"
    if kw.isupper() and re.search(r"[A-Z]", kw):
        return "acronym"
    return "word"


def _matched(text: str, keywords) -> list:
    """text 안에서 실제로 걸린 키워드 목록. text는 원문 대소문자를 유지해야 한다."""
    low = text.lower()
    out = []
    for kw in keywords:
        kind = _kind(kw)
        if kind == "hangul":
            hit = kw.lower() in low
        elif kind == "acronym":
            hit = bool(re.search(
                rf"(?<![A-Za-z0-9]){re.escape(kw)}(?![A-Za-z0-9])", text))
        else:
            hit = bool(re.search(
                rf"(?<![a-z0-9]){re.escape(kw.lower())}(?![a-z0-9])", low))
        if hit:
            out.append(kw)
    return out


def _has(text: str, keywords) -> bool:
    return bool(_matched(text, keywords))


# ── 개발자 트랙 ──────────────────────────────────────────
def is_developer_job(job: Job) -> bool:
    # 개발 트랙은 기존 동작 유지: 검색어 extra("스택")도 근거로 인정한다.
    # 워크넷은 본문까지 검색하므로, 제목에 스택이 없어도 그 스택을 쓰는 공고다.
    text = _text(job)

    # 제외 키워드가 있으면 탈락
    if _has(text, config.EXCLUDE_KEYWORDS):
        # 단, 개발 키워드가 확실히 있으면 살림 (예: "개발영업" 같은 오탐 방지)
        if not _has(text, ("개발", "developer", "engineer")):
            return False

    # 개발 키워드가 하나라도 있으면 통과
    if not _has(text, config.DEV_KEYWORDS):
        return False

    # 민간 공고는 관심 스택(FastAPI/Django/React 등)이 언급된 것만 통과
    if job.source in config.PRIVATE_SOURCES:
        if not _has(text, config.STACK_KEYWORDS):
            return False

    # 경력직만 보기 옵션 (민간 공고에만 적용)
    if config.EXPERIENCED_ONLY and job.source in config.PRIVATE_SOURCES:
        exp = job.experience or ""
        if "신입" in exp and "경력" not in exp:
            return False

    return True


# ── 교통 트랙 ────────────────────────────────────────────
def _transport_text(job: Job) -> str:
    """교통 판정용 텍스트. 질의어 extra를 제외하고, 복지 문구를 지운다.

    '교통비 지원'·'역세권' 같은 복지 안내를 안 지우면 무관한 공고가 전부 딸려온다.
    """
    # 공공기관·공무원은 기관명 자체가 교통 분야 지표다 (한국교통안전공단 등).
    # 민간은 사명이 우연히 겹치는 경우가 많아(위밋모빌리티, 한국교통대학교…)
    # 회사명을 근거에서 뺀다.
    text = _text(job, skip_extra_keys=QUERY_EXTRA_KEYS,
                 with_company=job.source not in config.PRIVATE_SOURCES)
    for phrase in config.TRANSPORT_NOISE_PHRASES:
        text = re.sub(re.escape(phrase), " ", text, flags=re.IGNORECASE)
    return text


def matched_certs(job: Job) -> tuple[list, bool]:
    """공고에서 발견한 우대 자격증 목록과, 교통기사 계열 여부를 반환."""
    text = _text(job, skip_extra_keys=QUERY_EXTRA_KEYS,
                 with_company=job.source not in config.PRIVATE_SOURCES)
    core = _matched(text, config.TRANSPORT_CERT_KEYWORDS)
    related = _matched(text, config.TRANSPORT_CERT_RELATED)
    return core + related, bool(core)


def is_transport_job(job: Job) -> bool:
    text = _transport_text(job)

    # 교통 분야 키워드가 없으면 탈락
    if not _has(text, config.TRANSPORT_KEYWORDS):
        return False

    _, starred = matched_certs(job)

    # 운전·배송직은 제외. 단 교통기사 계열 자격증 우대면 살린다.
    if _has(text, config.TRANSPORT_EXCLUDE_KEYWORDS) and not starred:
        return False

    # 개발 트랙의 일반 제외 키워드(영업/회계/간호…)도 그대로 적용
    if _has(text, config.EXCLUDE_KEYWORDS) and not starred:
        return False

    return True


# ── 통합 ────────────────────────────────────────────────
def classify(job: Job) -> Job:
    """job에 tracks / certs / cert_starred 를 채워서 그대로 반환."""
    tracks = []
    if config.ENABLE_DEV_TRACK and is_developer_job(job):
        tracks.append("dev")
    if config.ENABLE_TRANSPORT_TRACK and is_transport_job(job):
        tracks.append("transport")
    job.tracks = tracks

    if "transport" in tracks:
        job.certs, job.cert_starred = matched_certs(job)
    return job


def filter_jobs(jobs: list) -> list:
    """트랙이 하나라도 붙은 공고만 남긴다."""
    return [j for j in (classify(j) for j in jobs) if j.tracks]


def sort_for_send(jobs: list) -> list:
    """⭐(교통기사 우대) 공고를 앞으로. 그 외는 원래 순서 유지(안정 정렬).

    MAX_ITEMS_PER_RUN 으로 잘라낼 때 ⭐ 공고가 먼저 살아남게 하려는 목적.
    """
    return sorted(jobs, key=lambda j: not j.cert_starred)
