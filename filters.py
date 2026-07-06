"""개발자 공고인지 판별하는 필터."""
import config
from collectors import Job


def _haystack(job: Job) -> str:
    return " ".join([job.title, job.category, job.company]).lower()


def is_developer_job(job: Job) -> bool:
    text = _haystack(job)

    # 제외 키워드가 있으면 탈락
    if any(x.lower() in text for x in config.EXCLUDE_KEYWORDS):
        # 단, 개발 키워드가 확실히 있으면 살림 (예: "개발영업" 같은 오탐 방지)
        if not any(k.lower() in text for k in ("개발", "developer", "engineer")):
            return False

    # 개발 키워드가 하나라도 있으면 통과
    if not any(k.lower() in text for k in config.DEV_KEYWORDS):
        return False

    # 경력직만 보기 옵션 (민간 공고에만 적용)
    if config.EXPERIENCED_ONLY and job.source == "worknet":
        exp = job.experience or ""
        if "신입" in exp and "경력" not in exp:
            return False

    return True


def filter_jobs(jobs: list[Job]) -> list[Job]:
    return [j for j in jobs if is_developer_job(j)]
