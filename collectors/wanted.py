"""
원티드 채용정보 수집기 (민간 기업, 공식 OpenAPI).

공식 API: https://openapi.wanted.jobs/  (Jobs / Companies API 제공)
- 인증키 신청 후 메일로 발급(신청 접수 기준 3영업일 이내).
- Jobs API: 포지션 목록 조회 (필터: 정렬/연차/직원수/스킬/직군/직무)
- Companies API: 기업 상세 + 채용중 포지션 목록  ← '기업 정보 함께 받기'에 활용
- 크롤링이 아니라 공식 API이므로 약관 문제 없음.

⚠️ 정확한 엔드포인트 URL·인증 헤더·파라미터명·응답 필드명은
   발급받은 계정으로 https://openapi.wanted.jobs/api-docs/v1/ 문서를 보고 맞출 것.
   (아래는 일반적인 형태의 뼈대이며, TODO 부분을 문서 기준으로 채우면 된다.)
"""
import requests

from .base import Collector, Job

# TODO: api-docs 문서에서 실제 base host / path 확인
BASE_URL = "https://openapi.wanted.jobs/v1/jobs"

# 개발 직군/직무 필터. 문서의 Tags API로 실제 코드를 조회해 넣으면 정확도가 오른다.
# 값이 비어 있으면 전체를 받아 키워드 필터로 거른다.
JOB_GROUP = ""   # 예: 개발 직군 코드
JOB_TAGS = ""    # 예: 백엔드/프론트/풀스택 직무 코드(콤마 구분)


class WantedCollector(Collector):
    name = "wanted"

    def __init__(self, api_key: str, limit: int = 100):
        self.api_key = api_key
        self.limit = limit

    def fetch(self) -> list[Job]:
        # TODO: 문서 기준으로 인증 방식 확인 (헤더 X-API-KEY 또는 Bearer 등)
        headers = {"X-API-KEY": self.api_key, "Accept": "application/json"}
        params = {"limit": self.limit, "sort": "recent"}
        if JOB_GROUP:
            params["job_group"] = JOB_GROUP
        if JOB_TAGS:
            params["job_tags"] = JOB_TAGS

        try:
            resp = requests.get(BASE_URL, headers=headers, params=params, timeout=20)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            print(f"[wanted] 요청 실패: {e}")
            return []

        # 응답 구조는 문서 기준으로 확인. 흔한 형태: {"data":[{...}]} 또는 {"jobs":[...]}
        items = data.get("data") or data.get("jobs") or []

        jobs: list[Job] = []
        for it in items:
            title = it.get("position") or it.get("title") or ""
            company = (
                (it.get("company") or {}).get("name")
                if isinstance(it.get("company"), dict)
                else it.get("company_name", "")
            )
            if not title:
                continue
            job_id = it.get("id") or it.get("job_id") or ""
            url = it.get("url") or (
                f"https://www.wanted.co.kr/wd/{job_id}" if job_id else "https://www.wanted.co.kr/"
            )
            jobs.append(
                Job(
                    source=self.name,
                    title=title,
                    company=company or "",
                    url=url,
                    category=", ".join(it.get("skill_tags", []) or []) if isinstance(it.get("skill_tags"), list) else it.get("category", ""),
                    location=it.get("location", "") or (it.get("address", {}) or {}).get("location", ""),
                    experience=it.get("annual_range", "") or it.get("experience", ""),
                    deadline=it.get("due_time", "") or it.get("deadline", ""),
                    extra={},
                )
            )
        print(f"[wanted] 수집 {len(jobs)}건")
        return jobs
