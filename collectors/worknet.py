"""
고용24(워크넷) 채용정보 수집기 (민간 기업 개발자 공고) — 크롤링 방식.

오픈API 인증키가 개인에게 발급되지 않아, 채용정보 검색 결과 페이지를
하루 1회 읽는 방식으로 수집한다.

- robots.txt 확인 완료: 채용정보 목록/상세 경로(/wk/a/b/...)는 수집 허용.
- 정부 공공 사이트의 공개 채용정보, 비상업적 개인 용도, 저빈도(하루 1회) 호출.
- 키워드별로 최신순 1페이지(50건)씩만 읽는다. 요청 간 0.5초 대기.

⚠️ 사이트 개편으로 HTML 구조가 바뀌면 LIST_URL 과 파싱 로직을 조정할 것.
"""
import time

import requests
from bs4 import BeautifulSoup

from .base import Collector, Job
import config

BASE = "https://www.work24.go.kr"
LIST_URL = BASE + "/wk/a/b/1200/retriveDtlEmpSrchList.do"

# 검색 키워드 (각각 최신순 50건씩 조회 후 합침, 이후 filters.py 가 한 번 더 거름)
# 고용24 검색은 공고 본문까지 매칭되므로 스택명으로 검색하면
# 제목에 스택이 없어도 해당 스택을 쓰는 공고가 잡힌다.
STACK_SEARCH_KEYWORDS = [
    "fastapi", "django", "python", "파이썬", "react", "리액트",
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/122.0 Safari/537.36"
    )
}


class WorknetCollector(Collector):
    name = "worknet"

    def __init__(self, rows: int = 50):
        self.rows = rows

    def _search(self, keyword: str, kind: str = "스택") -> list[Job]:
        params = {
            "srcKeyword": keyword,
            "keyword": keyword,
            "resultCnt": self.rows,
            "sortField": "DATE",
            "sortOrderBy": "DESC",
            "pageIndex": 1,
        }
        resp = requests.get(LIST_URL, params=params, headers=HEADERS, timeout=35)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        jobs: list[Job] = []
        for link in soup.select("a[href*=empDetailAuthView]"):
            tr = link.find_parent("tr")
            if tr is None:
                continue
            tds = tr.find_all("td")
            if not tds:
                continue

            title = " ".join(link.get_text(strip=True).split())
            if not title:
                continue

            # td[0]: 회사명 + 제목(+버튼). 첫 텍스트 조각이 회사명.
            td0_parts = [p for p in tds[0].get_text("|", strip=True).split("|") if p]
            company = td0_parts[0] if td0_parts else ""

            # td[1]: 급여 | 경력 | 학력 | 근무지역 (항목 수는 공고마다 다를 수 있음)
            salary = experience = location = ""
            if len(tds) > 1:
                parts = [p for p in tds[1].get_text("|", strip=True).split("|") if p]
                if parts:
                    salary = parts[0]
                    location = parts[-1] if len(parts) > 1 else ""
                for p in parts:
                    if p.startswith(("경력", "신입")):
                        experience = p
                        break

            # td[2]: "마감일 : YYYY-MM-DD ..." 형태
            deadline = ""
            if len(tds) > 2:
                for p in tds[2].get_text("|", strip=True).split("|"):
                    if "마감일" in p:
                        deadline = p.split(":", 1)[-1].strip()
                        break

            jobs.append(
                Job(
                    source=self.name,
                    title=title,
                    company=company,
                    url=BASE + link["href"],
                    location=location,
                    experience=experience,
                    deadline=deadline,
                    salary=salary,
                    # 본문 매칭으로 잡힌 공고도 필터를 통과하도록 검색어를 기록.
                    # 개발 트랙의 스택 필터는 "스택" 키만 보므로, 교통 검색어는
                    # "검색어" 키에 넣어 개발 공고로 오분류되지 않게 한다.
                    extra={kind: keyword},
                )
            )
        return jobs

    def _search_terms(self) -> list[tuple[str, str]]:
        """(검색어, 종류) 목록. 켜져 있는 트랙만 조회한다."""
        terms: list[tuple[str, str]] = []
        if config.ENABLE_DEV_TRACK:
            terms += [(kw, "스택") for kw in STACK_SEARCH_KEYWORDS]
        if config.ENABLE_TRANSPORT_TRACK:
            terms += [(kw, "검색어") for kw in config.TRANSPORT_SEARCH_KEYWORDS]
        return terms

    def fetch(self) -> list[Job]:
        results: list[Job] = []
        for kw, kind in self._search_terms():
            try:
                results.extend(self._search(kw, kind))
            except Exception as e:
                print(f"[worknet] 검색 실패(keyword={kw}): {e}")
            time.sleep(0.5)  # 서버 부담 최소화

        # url 기준 중복 제거 (키워드 간 겹침 제거)
        seen, deduped = set(), []
        for j in results:
            if j.url in seen:
                continue
            seen.add(j.url)
            deduped.append(j)
        print(f"[worknet] 수집 {len(deduped)}건")
        return deduped