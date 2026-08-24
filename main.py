"""
개발자 채용공고 알림봇 — 메인.
수집 → 개발자 필터 → 중복 제거 → 텔레그램 발송 → 상태 저장.
"""
import config
from collectors import (
    WorknetCollector, AlioCollector, GosiCollector,
    SaraminCollector, WantedCollector,
)
from filters import filter_jobs, sort_for_send
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
    tracks = [
        n for n, on in (("개발", config.ENABLE_DEV_TRACK),
                        ("교통", config.ENABLE_TRANSPORT_TRACK)) if on
    ]
    print(f"=== 채용공고 수집 시작 (트랙: {', '.join(tracks) or '없음'}) ===")
    raw = collect_all()
    print(f"전체 수집: {len(raw)}건")

    matched = filter_jobs(raw)
    n_dev = sum(1 for j in matched if "dev" in j.tracks)
    n_tr = sum(1 for j in matched if "transport" in j.tracks)
    n_star = sum(1 for j in matched if j.cert_starred)
    print(f"필터 후: {len(matched)}건 "
          f"(개발 {n_dev} / 교통 {n_tr} / ⭐자격증우대 {n_star})")

    seen = storage.load_seen()
    new = storage.filter_new(matched, seen)
    print(f"신규(미발송) 공고: {len(new)}건")

    # ⭐(교통기사 우대) 공고가 잘려나가지 않게 먼저 정렬한 뒤 상한 적용
    new = sort_for_send(new)
    if len(new) > config.MAX_ITEMS_PER_RUN:
        dropped = len(new) - config.MAX_ITEMS_PER_RUN
        new = new[: config.MAX_ITEMS_PER_RUN]
        print(f"→ 상위 {config.MAX_ITEMS_PER_RUN}건만 발송 ({dropped}건 보류)")

    notifier.send(new)

    storage.mark_sent(new, seen)
    storage.save_seen(seen)
    print("=== 완료 ===")


if __name__ == "__main__":
    main()
