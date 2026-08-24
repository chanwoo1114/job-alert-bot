"""수집기 공통 요소: 표준 공고 데이터 모델."""
from dataclasses import dataclass, field, asdict
from typing import Optional
import hashlib


@dataclass
class Job:
    source: str                 # "worknet" | "alio" | "gosi" | "saramin" | "wanted"
    title: str                  # 공고 제목
    company: str                # 회사/기관명
    url: str                    # 상세 링크
    category: str = ""          # 직무/직종
    location: str = ""          # 근무지
    experience: str = ""        # 경력 조건
    deadline: str = ""          # 마감일
    salary: str = ""            # 급여
    extra: dict = field(default_factory=dict)  # 기관 정보 등 부가 데이터

    # ── 필터가 채우는 분류 정보 (수집기는 건드리지 않는다) ──
    tracks: list = field(default_factory=list)   # "dev" | "transport" (둘 다 가능)
    certs: list = field(default_factory=list)    # 공고에서 발견한 우대 자격증명
    cert_starred: bool = False                   # 교통기사 계열이면 True → ⭐ 최우선

    def uid(self) -> str:
        """중복 판정용 고유 키. url이 있으면 url, 없으면 source+title+company 해시."""
        base = self.url or f"{self.source}|{self.title}|{self.company}"
        return hashlib.sha1(base.encode("utf-8")).hexdigest()[:16]

    def to_dict(self) -> dict:
        return asdict(self)


class Collector:
    """모든 수집기가 상속하는 인터페이스."""
    name = "base"

    def fetch(self) -> list[Job]:
        raise NotImplementedError
