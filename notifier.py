"""텔레그램으로 공고를 발송한다."""
import html
import time

import requests

import config
from collectors import Job

API = "https://api.telegram.org/bot{token}/sendMessage"
TG_LIMIT = 3800  # 텔레그램 메시지 길이 안전선(실제 4096)

SOURCE_LABEL = {
    "wanted": "🟦 원티드",
    "saramin": "🟩 사람인",
    "worknet": "🏢 워크넷(민간)",
    "alio": "🏛 공공기관·공기업",
    "gosi": "📋 공무원 전산직",
}


def _format_job(job: Job) -> str:
    t = html.escape(job.title)
    c = html.escape(job.company)
    line = f"• <a href=\"{html.escape(job.url)}\"><b>{t}</b></a>\n  {c}"
    meta = []
    if job.location:
        meta.append(html.escape(job.location))
    if job.experience:
        meta.append(html.escape(job.experience))
    if job.deadline:
        meta.append(f"~{html.escape(job.deadline)}")
    if meta:
        line += "\n  " + " · ".join(meta)
    # 기관/기업 부가정보
    extra = " · ".join(
        f"{k}:{html.escape(str(v))}" for k, v in job.extra.items() if v
    )
    if extra:
        line += f"\n  <i>{extra}</i>"
    return line


def build_messages(jobs: list[Job]) -> list[str]:
    """소스별로 묶고 길이 제한에 맞춰 메시지들을 만든다."""
    if not jobs:
        return []

    today = time.strftime("%Y-%m-%d")
    grouped: dict[str, list[Job]] = {}
    for j in jobs:
        grouped.setdefault(j.source, []).append(j)

    header = f"☀️ <b>오늘의 개발자 채용공고</b> ({today}) — 총 {len(jobs)}건\n"
    messages, cur = [], header

    for source, items in grouped.items():
        section = f"\n<b>{SOURCE_LABEL.get(source, source)}</b> ({len(items)})\n"
        if len(cur) + len(section) > TG_LIMIT:
            messages.append(cur)
            cur = ""
        cur += section
        for j in items:
            block = _format_job(j) + "\n"
            if len(cur) + len(block) > TG_LIMIT:
                messages.append(cur)
                cur = ""
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
