"""
개발자 채용공고 알림봇 — 메인.
수집 → 개발자 필터 → 중복 제거 → 텔레그램 발송 → 상태 저장.
"""
import config
from collectors import (
    WorknetCollector, AlioCollector, GosiCollector,
    SaraminCollector, WantedCollector,
)
from filters import filter_jobs
import storage
import notifier


def collect_all():
    jobs = []

    if config.ENABLE_WANTED:
        if config.WANTED_API_KEY:
            jobs += WantedCollector(config.WANTED_API_KEY).fetch()
        else:
            print("[wanted] WANTED_API_KEY 없음 → 건너뜀")

    if config.ENABLE_SARAMIN:
        if config.SARAMIN_ACCESS_KEY:
            jobs += SaraminCollector(config.SARAMIN_ACCESS_KEY).fetch()
        else:
            print("[saramin] SARAMIN_ACCESS_KEY 없음 → 건너뜀")

    if config.ENABLE_WORKNET:
        jobs += WorknetCollector().fetch()

    if config.ENABLE_ALIO:
        if config.DATA_GO_KR_SERVICE_KEY:
            jobs += AlioCollector(config.DATA_GO_KR_SERVICE_KEY).fetch()
        else:
            print("[alio] DATA_GO_KR_SERVICE_KEY 없음 → 건너뜀")

    if config.ENABLE_GOSI:
        jobs += GosiCollector().fetch()

    return jobs


def main():
    print("=== 채용공고 수집 시작 ===")
    raw = collect_all()
    print(f"전체 수집: {len(raw)}건")

    dev = filter_jobs(raw)
    print(f"개발자 공고 필터 후: {len(dev)}건")

    seen = storage.load_seen()
    new = storage.filter_new(dev, seen)
    print(f"신규(미발송) 공고: {len(new)}건")

    # 너무 많으면 최신 위주로 잘라냄
    if len(new) > config.MAX_ITEMS_PER_RUN:
        new = new[: config.MAX_ITEMS_PER_RUN]
        print(f"→ 상위 {config.MAX_ITEMS_PER_RUN}건만 발송")

    notifier.send(new)

    storage.mark_sent(new, seen)
    storage.save_seen(seen)
    print("=== 완료 ===")


if __name__ == "__main__":
    main()
