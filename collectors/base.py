"""수집기 공통 요소: 표준 공고 데이터 모델."""
from dataclasses import dataclass, field, asdict
from typing import Optional
import hashlib


@dataclass
class Job:
    source: str                 # "worknet" | "alio" | "gosi"
    title: str                  # 공고 제목
    company: str                # 회사/기관명
    url: str                    # 상세 링크
    category: str = ""          # 직무/직종
    location: str = ""          # 근무지
    experience: str = ""        # 경력 조건
    deadline: str = ""          # 마감일
    salary: str = ""            # 급여
    extra: dict = field(default_factory=dict)  # 기관 정보 등 부가 데이터

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
