"""필터 회귀 테스트 — 의존성 없이 실행.

    PYTHONPATH=. python tests/test_filters.py

교통 트랙은 오탐이 나기 쉬운 구조라(복지 문구의 '교통비', 검색어 오염,
영어 단어 'its') 아래 케이스를 깨뜨리지 않는지 확인한다.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from collectors import Job          # noqa: E402
import filters                      # noqa: E402

# (설명, Job, 기대 트랙집합, 기대 ⭐)
CASES = [
    # ── 교통: 통과해야 함 ─────────────────────────────
    ("공공기관 교통기사 우대",
     Job("alio", "2026년 교통계획 분야 신입직원 채용 (교통기사 우대)",
         "한국교통안전공단", "u1", category="교통·물류"), {"transport"}, True),
    ("공무원 교통직",
     Job("gosi", "지방자치단체 교통시설 경력경쟁채용 시험공고",
         "행정안전부", "u2", category="공무원 교통·시설직"), {"transport"}, False),
    ("공기업 철도",
     Job("alio", "철도 신호설비 유지보수 직원 채용", "국가철도공단", "u3"),
     {"transport"}, False),
    ("공기업 — 제목엔 교통 없고 기관명만 교통 (공공은 기관명도 근거)",
     Job("alio", "2026년 상반기 신입직원 공개채용", "한국교통안전공단", "u3b"),
     {"transport"}, False),
    ("민간 교통 엔지니어링 + 자격증",
     Job("saramin", "교통영향평가 담당자 모집 (교통기사·도시계획기사 필수)",
         "OO엔지니어링", "u4", experience="경력 3년"), {"transport"}, True),
    ("민간 ITS",
     Job("worknet", "ITS 교통신호 시스템 운영 담당", "OO정보통신", "u5",
         extra={"검색어": "ITS"}), {"transport"}, False),
    ("관련 자격증만 → ⭐ 아님",
     Job("alio", "도시계획 분야 채용 (도시계획기사 우대)", "OO공사", "u6"),
     {"transport"}, False),
    ("철도 토목설계 엔지니어",
     Job("worknet", "철도사업부 토목(철도)설계 엔지니어 모집", "(주)렉스이엔씨",
         "u6b", extra={"검색어": "교통계획"}), {"transport"}, False),

    # ── 교통: 걸러져야 함 (실제 라이브 실행에서 터진 오탐) ──
    ("복지 문구의 교통비/역세권만 있는 회계 공고",
     Job("saramin", "회계 담당자 모집", "OO상사", "u7",
         extra={"복지": "교통비 지원, 역세권, 셔틀버스 운행"}), set(), False),
    ("역세권 자랑하는 간호 공고",
     Job("worknet", "간호조무사 모집 (역세권, 주차 가능)", "OO의원", "u8"),
     set(), False),
    ("버스 운전기사",
     Job("worknet", "시내버스 운전기사 채용", "OO운수", "u9",
         category="버스노선 운행"), set(), False),
    ("택배 배송",
     Job("worknet", "택배 배송기사 모집 (도로 주행)", "OO택배", "u10"),
     set(), False),
    ("검색어가 '교통기사'였을 뿐 내용은 무관 → 탈락, ⭐ 아님",
     Job("worknet", "컴퓨터 유지보수 직원 모집", "㈜이노텍코리아", "u15",
         extra={"검색어": "교통기사"}), set(), False),
    ("검색어가 'ITS'였을 뿐인 반도체 물류",
     Job("worknet", "반도체 장비 입출고관리(지게차)", "㈜진영물류산업", "u16",
         extra={"검색어": "ITS"}), set(), False),
    ("영어 단어 'its' 는 ITS 로 매칭되지 않음",
     Job("saramin", "Improve its performance and transition plan",
         "Foo Corp", "u17"), set(), False),
    ("'transition' 은 transit 으로 매칭되지 않음",
     Job("saramin", "Digital transition specialist", "Foo", "u18"),
     set(), False),
    ("민간 — 사명만 교통 관련 (위밋모빌리티 등) → 탈락",
     Job("worknet", "총무 담당자 모집", "위밋모빌리티", "u19"), set(), False),
    ("마을버스 정비보조원",
     Job("worknet", "마을버스 정비보조원", "（주）오성", "u20",
         extra={"검색어": "교통기사"}), set(), False),

    # ── 개발: 기존 동작 유지 ─────────────────────────
    ("공공 전산직",
     Job("alio", "전산직 신입 채용", "OO공단", "u11"), {"dev"}, False),
    ("민간 스택 매칭",
     Job("saramin", "백엔드 개발자 (Django)", "OO테크", "u12",
         extra={"기술": "django, python"}), {"dev"}, False),
    ("민간 개발자인데 관심 스택 아님 → 탈락",
     Job("saramin", "백엔드 개발자 (Java Spring)", "OO테크", "u13",
         extra={"기술": "java, spring"}), set(), False),
    ("교통 SI 개발 → 두 트랙 동시",
     Job("worknet", "교통정보 시스템 백엔드 개발자 (Python/Django)",
         "OO소프트", "u14", extra={"스택": "django"}),
     {"dev", "transport"}, False),
]


def run() -> int:
    fails = 0
    for desc, job, want_tracks, want_star in CASES:
        j = filters.classify(job)
        got = set(j.tracks)
        ok = got == want_tracks and j.cert_starred == want_star
        if not ok:
            fails += 1
        print(f"{'✅' if ok else '❌'} {desc}")
        if not ok:
            print(f"     기대: tracks={sorted(want_tracks)} star={want_star}")
            print(f"     실제: tracks={sorted(got)} star={j.cert_starred} "
                  f"certs={j.certs}")

    # ⭐ 공고가 정렬에서 앞으로 오는지
    jobs = [filters.classify(j) for _, j, _, _ in CASES]
    jobs = [j for j in jobs if j.tracks]
    ordered = filters.sort_for_send(jobs)
    starred = [j for j in ordered if j.cert_starred]
    if starred and ordered[:len(starred)] != starred:
        print("❌ sort_for_send: ⭐ 공고가 앞으로 오지 않음")
        fails += 1
    else:
        print("✅ sort_for_send: ⭐ 공고 우선 정렬")

    print(f"\n{len(CASES) + 1 - fails}/{len(CASES) + 1} 통과")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(run())
