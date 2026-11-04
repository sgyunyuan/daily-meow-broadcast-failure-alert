#!/usr/bin/env python3
"""Broadcast one daily message and notify Shangguan only when broadcasting fails."""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

BROADCAST_ENDPOINT = "http://api.chuckfang.com:12580/subscribe/openBroadcast"
FAILURE_NOTIFY_ENDPOINT = "https://api.chuckfang.com/shangguan/"
TIMEZONE = ZoneInfo("Asia/Shanghai")


class BroadcastFailure(Exception):
    """A broadcast request or API response indicates failure."""


def read_text(path: str, fallback: str) -> str:
    try:
        text = Path(path).read_text(encoding="utf-8-sig").strip()
        return text or fallback
    except OSError:
        return fallback


def call_api(url: str, *, method: str, body: bytes | None = None, content_type: str | None = None) -> tuple[int, bytes]:
    headers = {"User-Agent": "daily-meow-broadcast-failure-alert/1.0"}
    if content_type:
        headers["Content-Type"] = content_type
    request = Request(url, data=body, headers=headers, method=method)
    try:
        with urlopen(request, timeout=30) as response:
            return response.status, response.read()
    except HTTPError as exc:
        return exc.code, exc.read()
    except (URLError, TimeoutError, OSError) as exc:
        reason = getattr(exc, "reason", None)
        safe_reason = str(reason) if reason else type(exc).__name__
        raise BroadcastFailure(f"网络请求失败：{safe_reason}") from None


def safe_reason(reason: str, channel_id: str, union_id: str) -> str:
    # These values are passed in the broadcast URL query and must never appear in logs or alerts.
    for secret in (channel_id, union_id):
        if secret:
            reason = reason.replace(secret, "[已隐藏]")
    return reason.strip()[:1200]


def send_failure_notification(channel_name: str, content: str, reason: str, failed_at: datetime) -> bool:
    notice = (
        f"广播失败\n"
        f"频道名称：{channel_name}\n"
        f"广播内容：{content}\n"
        f"失败原因：{reason}\n"
        f"失败时间：{failed_at:%Y-%m-%d %H:%M:%S} 北京时间"
    )
    form = urlencode({"title": "频道广播失败", "msg": notice}).encode("utf-8")
    try:
        status, raw = call_api(
            FAILURE_NOTIFY_ENDPOINT,
            method="POST",
            body=form,
            content_type="application/x-www-form-urlencoded; charset=utf-8",
        )
    except BroadcastFailure as exc:
        print(f"Failure notification could not be sent: {exc}", file=sys.stderr)
        return False

    response_text = raw.decode("utf-8", errors="replace")
    try:
        result = json.loads(response_text)
    except json.JSONDecodeError:
        result = {}
    if not 200 <= status < 300 or result.get("status") != 200:
        print(f"Failure notification API returned HTTP {status}: {response_text[:500]}", file=sys.stderr)
        return False
    print("Failure notification sent successfully.")
    return True


def main() -> int:
    channel_name = read_text("content/channel_name.txt", "未配置频道名称")
    channel_id = os.environ.get("CHANNEL_ID", "").strip()
    union_id = os.environ.get("UNION_ID", "").strip()
    now = datetime.now(TIMEZONE)
    content_template = read_text("content/daily_message.txt", "（无法读取广播文案）")
    content = content_template.replace("{date}", now.strftime("%Y-%m-%d"))

    try:
        if not channel_id or not union_id:
            raise BroadcastFailure("缺少必需的 GitHub Actions Secrets：CHANNEL_ID 或 UNION_ID")

        params = urlencode({"channelId": channel_id, "unionId": union_id})
        status, raw = call_api(
            f"{BROADCAST_ENDPOINT}?{params}",
            method="POST",
            body=content.encode("utf-8"),
            content_type="text/plain; charset=utf-8",
        )
        response_text = raw.decode("utf-8", errors="replace")
        if not 200 <= status < 300:
            raise BroadcastFailure(f"广播接口返回 HTTP {status}：{response_text[:1000]}")
        try:
            result = json.loads(response_text)
        except json.JSONDecodeError:
            raise BroadcastFailure(f"广播接口响应不是有效 JSON：{response_text[:1000]}") from None
        if result.get("status") != 200 or result.get("data") is not True:
            detail = str(result.get("msg", result))
            raise BroadcastFailure(f"广播接口报告失败：{detail[:1000]}")

        print("Broadcast succeeded. No result notification is sent on success.")
        return 0
    except BroadcastFailure as exc:
        failed_at = datetime.now(TIMEZONE)
        reason = safe_reason(str(exc), channel_id, union_id)
        send_failure_notification(channel_name, content, reason, failed_at)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
