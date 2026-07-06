"""
이미 보낸 공고를 기록해 중복 발송을 막는다.
GitHub Actions에서는 실행 후 seen.json 을 커밋해 상태를 유지한다.
오래된 기록은 자동으로 정리한다(최근 2000건만 유지).
"""
import json
import os
import time

import config

MAX_KEEP = 2000


def load_seen() -> dict:
    if not os.path.exists(config.SEEN_PATH):
        return {}
    try:
        with open(config.SEEN_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_seen(seen: dict) -> None:
    # 최근 항목만 유지 (timestamp 기준 정렬 후 자르기)
    if len(seen) > MAX_KEEP:
        items = sorted(seen.items(), key=lambda kv: kv[1], reverse=True)[:MAX_KEEP]
        seen = dict(items)
    os.makedirs(os.path.dirname(config.SEEN_PATH), exist_ok=True)
    with open(config.SEEN_PATH, "w", encoding="utf-8") as f:
        json.dump(seen, f, ensure_ascii=False, indent=0)


def filter_new(jobs, seen: dict):
    """아직 보내지 않은 공고만 반환."""
    new = []
    for j in jobs:
        if j.uid() not in seen:
            new.append(j)
    return new


def mark_sent(jobs, seen: dict) -> None:
    now = int(time.time())
    for j in jobs:
        seen[j.uid()] = now
