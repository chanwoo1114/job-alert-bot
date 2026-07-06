"""
워크넷(고용24) 채용정보 수집기 (민간 기업 개발자 공고).

⚠️ 이 API는 공공데이터포털(data.go.kr) 키가 아니라
   고용24 오픈API(https://www.work24.go.kr → 고용24 오픈API → 인증키 신청)에서
   발급받는 별도 authKey 가 필요하다. .env 의 WORK24_AUTH_KEY 에 넣을 것.

   (공공기관 채용은 alio.py 가 data.go.kr 키로 수집하므로 이 키가 없어도
    공공기관/공무원 공고는 정상 동작한다.)
"""
import requests
import xml.etree.ElementTree as ET

from .base import Collector, Job
import config

# 고용24 채용정보 목록 API. 인증키 발급 후 명세서의 '요청주소'와 다르면 맞춰 수정.
BASE_URL = "https://www.work24.go.kr/cm/openApi/call/wk/callOpenApiSvcInfo210L01.do"

# 개발/전산 관련 직종코드 (워크넷 직종코드 '정보통신' 계열).
# 명세서의 공통코드(직종코드) API로 정확한 코드를 조회해 넣으면 정확도가 올라간다.
# 코드를 비워두면 키워드 필터로만 거른다.
JOB_CODES = []  # 예: ["133", "134"]


def _text(node, *tags, default=""):
    """여러 후보 태그명 중 먼저 값이 있는 것을 반환 (명세 버전차 대응)."""
    for tag in tags:
        el = node.find(tag)
        if el is not None and el.text:
            return el.text.strip()
    return default


class WorknetCollector(Collector):
    name = "worknet"

    def __init__(self, auth_key: str, rows: int = 100):
        self.auth_key = auth_key
        self.rows = rows

    def _request(self, job_code: str | None = None) -> list[Job]:
        params = {
            "authKey": self.auth_key,
            "callTp": "L",                 # L: 목록
            "returnType": "XML",
            "startPage": 1,
            "display": self.rows,
        }
        if job_code:
            params["occupation"] = job_code

        resp = requests.get(BASE_URL, params=params, timeout=20)
        resp.raise_for_status()

        jobs: list[Job] = []
        root = ET.fromstring(resp.content)
        # 오류 응답이면 메시지 출력
        err = root.find(".//message") if root.tag in ("error", "Error") else None
        if err is not None:
            print(f"[worknet] API 오류: {err.text}")
            return []

        # 응답 구조: <wantedRoot><wanted>...</wanted></wantedRoot>
        for item in root.iter("wanted"):
            title = _text(item, "title", "empWantedTitle")
            company = _text(item, "company", "empBusiNm")
            if not title:
                continue
            url = _text(
                item,
                "wantedInfoUrl", "wantedMobileUrl",
                "empWantedHomepgDetail", "empWantedMobileUrl",
                default="https://www.work24.go.kr/",
            )
            jobs.append(
                Job(
                    source=self.name,
                    title=title,
                    company=company,
                    url=url,
                    category=_text(item, "jobsNm", "empWantedTypeNm"),
                    location=_text(item, "region", "regionNm", "basicAddr"),
                    experience=_text(item, "career", "empWantedCareerNm"),
                    deadline=_text(item, "closeDt", "empWantedEndt"),
                    salary=_text(item, "sal", "salTpNm"),
                )
            )
        return jobs

    def fetch(self) -> list[Job]:
        results: list[Job] = []
        codes = JOB_CODES or [None]  # 코드가 없으면 전체 조회 후 키워드 필터
        for code in codes:
            try:
                results.extend(self._request(code))
            except Exception as e:
                print(f"[worknet] 요청 실패(code={code}): {e}")
        # url 기준 중복 제거
        seen, deduped = set(), []
        for j in results:
            if j.url in seen:
                continue
            seen.add(j.url)
            deduped.append(j)
        print(f"[worknet] 수집 {len(deduped)}건")
        return deduped