"""
공무원 전산직 공고 수집기.

사이버국가고시센터(gosi.kr)가 국가공무원채용시스템(gongmuwon.gosi.kr)으로
개편되어, 경력경쟁채용 시험공고 목록을 읽어온다.

⚠️ 정부 사이트는 개편이 잦다. 게시판 URL/HTML 구조가 바뀌면
   LIST_URL 과 아래 파싱 로직을 조정해야 한다.
   기본 동작은 '제목에 전산/정보/데이터가 들어간 공고'만 통과.
"""
import re
import time
from datetime import date

import requests
from bs4 import BeautifulSoup

from .base import Collector, Job
import config

# 국가공무원채용시스템 > 채용정보 > 시험공고 (경력경쟁채용)
LIST_URL = "https://gongmuwon.gosi.kr/crrut/RpaApTestPbancLst.do"
DETAIL_URL = "https://gongmuwon.gosi.kr/crrut/RpaApTestPbancDtl.do"

# 공무원 공고 중 전산 계열
DEV_KEYS = ["전산", "정보보호", "정보처리", "데이터", "정보통신", "정보관리"]


def _keys() -> list[str]:
    """켜져 있는 트랙에 해당하는 직렬 키워드만 모은다."""
    keys = []
    if config.ENABLE_DEV_TRACK:
        keys += DEV_KEYS
    if config.ENABLE_TRANSPORT_TRACK:
        keys += config.GOSI_TRANSPORT_KEYS
    return keys

# "26.08.25.(화)~ 26.08.28.(금)" 형태에서 마지막 날짜를 뽑는다
_DATE_RE = re.compile(r"(\d{2})\.(\d{2})\.(\d{2})\.")


def _end_date(period: str):
    """접수기간 문자열의 종료일. 못 읽으면 None."""
    found = _DATE_RE.findall(period or "")
    if not found:
        return None
    yy, mm, dd = found[-1]
    try:
        return date(2000 + int(yy), int(mm), int(dd))
    except ValueError:
        return None


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/122.0 Safari/537.36"
    )
}


class GosiCollector(Collector):
    name = "gosi"

    # 교통 계열 직렬은 전산직보다 드물어서 1페이지(10건)만 보면 놓친다.
    # 다만 뒤쪽 페이지는 이미 마감된 공고라, 마감 페이지를 만나면 멈춘다.
    def __init__(self, max_pages: int = 5):
        self.max_pages = max_pages

    def _rows(self, session, page: int):
        """한 페이지의 공고 행 목록. 실패하면 None."""
        try:
            if page == 1:
                resp = session.get(LIST_URL, timeout=20)
            else:
                # 페이징은 폼 POST (hdn_curr_page)
                resp = session.post(
                    LIST_URL, data={"hdn_curr_page": page}, timeout=25
                )
            resp.raise_for_status()
        except Exception as e:
            print(f"[gosi] 요청 실패(page={page}): {e}")
            return None
        soup = BeautifulSoup(resp.text, "html.parser")
        return soup.select("ul.tbody[id^=addNtc_]")

    def fetch(self) -> list[Job]:
        keys = _keys()
        if not keys:
            return []

        today = date.today()
        session = requests.Session()
        session.headers.update(HEADERS)

        jobs: list[Job] = []
        for page in range(1, self.max_pages + 1):
            rows = self._rows(session, page)
            if not rows:
                break

            page_live = 0
            for row in rows:
                rcrut_id = row.get("id", "").removeprefix("addNtc_")
                title_input = row.select_one("input[name=testNm]")
                title = (title_input.get("value") or "").strip() if title_input else ""
                if not title or len(title) < 5:
                    continue

                apply_period = row.select_one("li[data-title=원서접수기간] div")
                deadline = ""
                if apply_period:
                    deadline = " ".join(apply_period.get_text(strip=True).split())

                # 접수 마감된 공고는 건너뛴다 (뒤쪽 페이지는 대부분 마감분)
                end = _end_date(deadline)
                if end and end < today:
                    continue
                page_live += 1

                if not any(k in title for k in keys):
                    continue

                inst = row.select_one("li.logo div")
                company = (
                    inst.get_text(strip=True) if inst else "국가공무원 (인사혁신처)"
                )

                jobs.append(
                    Job(
                        source=self.name,
                        title=title,
                        company=company,
                        url=f"{DETAIL_URL}?rcrutNtId={rcrut_id}",
                        category=(
                            "공무원 전산직"
                            if any(k in title for k in DEV_KEYS)
                            else "공무원 교통·시설직"
                        ),
                        deadline=deadline,
                    )
                )

            # 이 페이지 전체가 마감분이면 더 뒤는 볼 필요 없다
            if page_live == 0:
                break
            time.sleep(0.4)

        # 제목 기준 중복 제거
        seen, deduped = set(), []
        for j in jobs:
            if j.title in seen:
                continue
            seen.add(j.title)
            deduped.append(j)
        print(f"[gosi] 수집 {len(deduped)}건")
        return deduped
