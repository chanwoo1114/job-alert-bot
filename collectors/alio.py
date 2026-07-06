"""
공공기관 채용정보 수집기 (공기업/공공기관 개발자 공고).

데이터: 공공데이터포털 '기획재정부_공공기관 채용정보 조회서비스'
        https://www.data.go.kr/data/15125273/openapi.do
        (원본: 잡알리오 job.alio.go.kr)

⚠️ 엔드포인트/파라미터/필드명은 활용신청 후 받는 명세서 기준으로 확인할 것.
   JSON 응답을 지원하므로 여기서는 JSON 파싱 기준으로 작성.
"""
import requests

from .base import Collector, Job
import config

# 인사혁신처_공공기관 채용정보 목록 API (실제 응답 확인 완료)
BASE_URL = "https://apis.data.go.kr/1051000/recruitment/list"


class AlioCollector(Collector):
    name = "alio"

    def __init__(self, service_key: str, rows: int = 100):
        self.service_key = service_key
        self.rows = rows

    def fetch(self) -> list[Job]:
        params = {
            "serviceKey": self.service_key,
            "numOfRows": self.rows,
            "pageNo": 1,
            "resultType": "json",
            # 접수중인 공고만
            "ongoingYn": "Y",
        }
        try:
            resp = requests.get(BASE_URL, params=params, timeout=20)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            print(f"[alio] 요청 실패: {e}")
            return []

        # 응답 구조: {"resultCode": 200, "totalCount": n, "result": [ {...}, ... ]}
        if data.get("resultCode") != 200:
            print(f"[alio] API 오류: {data.get('resultCode')} {data.get('resultMsg')}")
            return []
        items = data.get("result") or []

        jobs: list[Job] = []
        for it in items:
            title = it.get("recrutPbancTtl") or it.get("title") or ""
            org = it.get("instNm") or it.get("company") or ""
            if not title:
                continue
            sn = it.get("recrutPblntSn") or it.get("sn") or ""
            url = (
                it.get("srcUrl")
                or (f"https://job.alio.go.kr/recruitview.do?systemKindCode=&idx={sn}"
                    if sn else "https://job.alio.go.kr/recruit.do")
            )
            jobs.append(
                Job(
                    source=self.name,
                    title=title,
                    company=org,
                    url=url,
                    category=it.get("ncsCdNmLst") or it.get("hireTypeNmLst") or "",
                    location=it.get("workRgnNmLst") or "",
                    experience=it.get("recrutSeNm") or "",   # 신입/경력
                    deadline=it.get("pbancEndYmd") or "",
                    extra={
                        "기관유형": it.get("instTyNm") or "",
                        "주무부처": it.get("compDeadEnd") or it.get("govNm") or "",
                    },
                )
            )
        print(f"[alio] 수집 {len(jobs)}건")
        return jobs
