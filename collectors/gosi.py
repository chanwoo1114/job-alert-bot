"""
공무원 전산직 공고 수집기.

사이버국가고시센터(gosi.kr)가 국가공무원채용시스템(gongmuwon.gosi.kr)으로
개편되어, 경력경쟁채용 시험공고 목록을 읽어온다.

⚠️ 정부 사이트는 개편이 잦다. 게시판 URL/HTML 구조가 바뀌면
   LIST_URL 과 아래 파싱 로직을 조정해야 한다.
   기본 동작은 '제목에 전산/정보/데이터가 들어간 공고'만 통과.
"""
import requests
from bs4 import BeautifulSoup

from .base import Collector, Job

# 국가공무원채용시스템 > 채용정보 > 시험공고 (경력경쟁채용)
LIST_URL = "https://gongmuwon.gosi.kr/crrut/RpaApTestPbancLst.do"
DETAIL_URL = "https://gongmuwon.gosi.kr/crrut/RpaApTestPbancDtl.do"

# 공무원 공고 중 전산 계열만 추림
KEYS = ["전산", "정보보호", "정보처리", "데이터", "정보통신", "정보관리"]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/122.0 Safari/537.36"
    )
}


class GosiCollector(Collector):
    name = "gosi"

    def fetch(self) -> list[Job]:
        try:
            resp = requests.get(LIST_URL, headers=HEADERS, timeout=20)
            resp.raise_for_status()
        except Exception as e:
            print(f"[gosi] 요청 실패: {e}")
            return []

        soup = BeautifulSoup(resp.text, "html.parser")
        jobs: list[Job] = []

        # 각 공고는 <ul id="addNtc_<공고ID>" class="tbody"> 행으로 렌더링된다.
        # 제목은 <input name="testNm" value="...">, 기관명은 li.logo 안 div.
        for row in soup.select("ul.tbody[id^=addNtc_]"):
            rcrut_id = row.get("id", "").removeprefix("addNtc_")
            title_input = row.select_one("input[name=testNm]")
            title = (title_input.get("value") or "").strip() if title_input else ""
            if not title or len(title) < 5:
                continue
            if not any(k in title for k in KEYS):
                continue

            inst = row.select_one("li.logo div")
            company = inst.get_text(strip=True) if inst else "국가공무원 (인사혁신처)"

            apply_period = row.select_one("li[data-title=원서접수기간] div")
            deadline = ""
            if apply_period:
                deadline = " ".join(apply_period.get_text(strip=True).split())

            jobs.append(
                Job(
                    source=self.name,
                    title=title,
                    company=company,
                    url=f"{DETAIL_URL}?rcrutNtId={rcrut_id}",
                    category="공무원 전산직",
                    deadline=deadline,
                )
            )

        # 제목 기준 중복 제거
        seen, deduped = set(), []
        for j in jobs:
            if j.title in seen:
                continue
            seen.add(j.title)
            deduped.append(j)
        print(f"[gosi] 수집 {len(deduped)}건")
        return deduped