"""
사람인 채용정보 수집기 (민간 기업, 공식 API).

공식 API: https://oapi.saramin.co.kr  (채용공고 검색 API)
- 이용신청 후 access-key 발급 (개발자용 무료, 하루 500회 호출)
- 크롤링이 아니라 사람인이 공식 제공하는 API이므로 약관 문제 없음.

응답 예시(JSON):
{ "jobs": { "count":N, "job":[ {
    "url":"...", "active":1,
    "company":{"detail":{"name":"..","href":".."}},
    "position":{"title":"..","location":{"name":".."},
                "experience-level":{"name":"경력 2~3년"},
                "job-code":{"name":".."}},
    "keyword":"..", "salary":{"name":".."},
    "expiration-date":"YYYY-MM-DD" } ] } }
"""
import requests

from .base import Collector, Job

BASE_URL = "https://oapi.saramin.co.kr/job-search"

# 개발자 공고를 좁히는 검색어 (공백/콤마로 복수 지정)
DEFAULT_KEYWORDS = "백엔드,프론트엔드,풀스택,서버개발,웹개발,소프트웨어"


def _name(d: dict, *path, default=""):
    """중첩 dict에서 name 값을 안전하게 꺼낸다."""
    cur = d
    for p in path:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(p, {})
    if isinstance(cur, dict):
        return cur.get("name", default)
    return cur or default


class SaraminCollector(Collector):
    name = "saramin"

    def __init__(self, access_key: str, keywords: str = DEFAULT_KEYWORDS, count: int = 100):
        self.access_key = access_key
        self.keywords = keywords
        self.count = count  # 최대 110

    def fetch(self) -> list[Job]:
        params = {
            "access-key": self.access_key,
            "keywords": self.keywords,
            "count": self.count,
            "start": 1,
            "sort": "pd",        # 최신 등록일순
            "fields": "expiration-date,company-keyword",
        }
        headers = {"Accept": "application/json"}
        try:
            resp = requests.get(BASE_URL, params=params, headers=headers, timeout=20)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            print(f"[saramin] 요청 실패: {e}")
            return []

        job_list = data.get("jobs", {}).get("job", [])
        if isinstance(job_list, dict):  # 결과 1건일 때 dict로 오는 경우 방어
            job_list = [job_list]

        jobs: list[Job] = []
        for it in job_list:
            pos = it.get("position", {})
            title = _name({"x": pos}, "x", "title") or pos.get("title", "")
            if not title:
                continue
            jobs.append(
                Job(
                    source=self.name,
                    title=title,
                    company=_name(it, "company", "detail"),
                    url=it.get("url", "https://www.saramin.co.kr/"),
                    category=_name(pos, "job-code") or _name(pos, "job-mid-code"),
                    location=_name(pos, "location"),
                    experience=_name(pos, "experience-level"),
                    deadline=it.get("expiration-date", ""),
                    salary=_name(it, "salary"),
                    extra={"기술": it.get("keyword", "")},
                )
            )
        print(f"[saramin] 수집 {len(jobs)}건")
        return jobs
