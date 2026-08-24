"""텔레그램으로 공고를 발송한다."""
import html
import time

import requests

import config
import filters
from collectors import Job

API = "https://api.telegram.org/bot{token}/sendMessage"
TG_LIMIT = 3800  # 텔레그램 메시지 길이 안전선(실제 4096)

SOURCE_LABEL = {
    "wanted": "🟦 원티드",
    "saramin": "🟩 사람인",
    "worknet": "🏢 워크넷(민간)",
    "alio": "🏛 공공기관·공기업",
    "gosi": "📋 공무원",
}

# 트랙 표시 순서 — 교통을 먼저 보여준다
TRACK_ORDER = ["transport", "dev"]
TRACK_LABEL = {
    "transport": "🚦 교통 분야",
    "dev": "💻 개발자",
}


def _format_job(job: Job) -> str:
    t = html.escape(job.title)
    c = html.escape(job.company)
    bullet = "⭐" if job.cert_starred else "•"
    line = f"{bullet} <a href=\"{html.escape(job.url)}\"><b>{t}</b></a>\n  {c}"
    meta = []
    if job.location:
        meta.append(html.escape(job.location))
    if job.experience:
        meta.append(html.escape(job.experience))
    if job.deadline:
        meta.append(f"~{html.escape(job.deadline)}")
    if meta:
        line += "\n  " + " · ".join(meta)
    # 우대 자격증 (교통기사 계열은 ⭐로 이미 표시됨)
    if job.certs:
        line += "\n  🎫 " + " · ".join(html.escape(c) for c in job.certs)
    # 기관/기업 부가정보 (내부 질의어는 읽는 사람에게 의미 없으므로 숨김)
    extra = " · ".join(
        f"{k}:{html.escape(str(v))}"
        for k, v in job.extra.items()
        if v and k not in filters.QUERY_EXTRA_KEYS
    )
    if extra:
        line += f"\n  <i>{extra}</i>"
    return line


def build_messages(jobs: list[Job]) -> list[str]:
    """트랙 → 소스 순으로 묶고 길이 제한에 맞춰 메시지들을 만든다."""
    if not jobs:
        return []

    today = time.strftime("%Y-%m-%d")
    starred = sum(1 for j in jobs if j.cert_starred)

    # 트랙별 분류 (dev/transport 둘 다 걸린 공고는 교통 쪽에만 한 번 넣는다)
    by_track: dict[str, list[Job]] = {}
    for j in jobs:
        track = "transport" if "transport" in j.tracks else "dev"
        by_track.setdefault(track, []).append(j)

    counts = " · ".join(
        f"{TRACK_LABEL[t]} {len(by_track[t])}건"
        for t in TRACK_ORDER if by_track.get(t)
    )
    header = f"☀️ <b>오늘의 채용공고</b> ({today}) — 총 {len(jobs)}건\n"
    if counts:
        header += f"{counts}\n"
    if starred:
        header += f"⭐ 교통기사 계열 자격증 우대 {starred}건\n"

    messages, cur = [], header

    def flush_if_needed(addition: str) -> None:
        nonlocal cur
        if len(cur) + len(addition) > TG_LIMIT:
            messages.append(cur)
            cur = ""

    for track in TRACK_ORDER:
        items = by_track.get(track)
        if not items:
            continue

        track_head = f"\n<b>━ {TRACK_LABEL[track]} ━</b>\n"
        flush_if_needed(track_head)
        cur += track_head

        # 트랙 안에서 소스별로 묶고, ⭐ 공고를 앞으로
        grouped: dict[str, list[Job]] = {}
        for j in items:
            grouped.setdefault(j.source, []).append(j)

        for source, group in grouped.items():
            section = f"\n<b>{SOURCE_LABEL.get(source, source)}</b> ({len(group)})\n"
            flush_if_needed(section)
            cur += section
            for j in sorted(group, key=lambda x: not x.cert_starred):
                block = _format_job(j) + "\n"
                flush_if_needed(block)
                cur += block

    if cur.strip():
        messages.append(cur)
    return messages


def send(jobs: list[Job]) -> None:
    if not config.TELEGRAM_BOT_TOKEN or not config.TELEGRAM_CHAT_IDS:
        raise RuntimeError("TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_IDS 가 설정되지 않았습니다.")

    messages = build_messages(jobs)
    if not messages:
        # 새 공고가 없으면 조용히 넘어감 (원하면 '오늘 새 공고 없음' 알림 추가 가능)
        print("발송할 새 공고가 없습니다.")
        return

    url = API.format(token=config.TELEGRAM_BOT_TOKEN)
    for chat_id in config.TELEGRAM_CHAT_IDS:
        for msg in messages:
            resp = requests.post(
                url,
                json={
                    "chat_id": chat_id,
                    "text": msg,
                    "parse_mode": "HTML",
                    "disable_web_page_preview": True,
                },
                timeout=20,
            )
            if resp.status_code != 200:
                print(f"[telegram] 발송 실패({chat_id}): {resp.status_code} {resp.text}")
            time.sleep(0.4)  # rate limit 회피
    print(f"발송 완료: {len(messages)}개 메시지 → {len(config.TELEGRAM_CHAT_IDS)}명")
