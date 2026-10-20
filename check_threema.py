#!/usr/bin/env python3
"""Meldet neue Threema-iOS-Tags (z. B. 7.4.3b74302) per Telegram.

Benachrichtigt nur zu Bürozeiten (Mo-Fr, 08:00-17:30 lokale Zeit).
Ausserhalb davon passiert nichts; der nächste Lauf im Zeitfenster holt es nach.
"""
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, time
from pathlib import Path
from zoneinfo import ZoneInfo

REPO_URL = "https://github.com/threema-ch/threema-ios"
STATE_FILE = Path(__file__).parent / "state" / "last_build.txt"
TAG_RE = re.compile(r"^(?P<version>[\d.]+)b(?P<build>\d+)$")

TZ = ZoneInfo(os.environ.get("TIMEZONE", "Europe/Zurich"))
OFFICE_START = time(8, 0)
OFFICE_END = time(17, 30)


def in_office_hours(now: datetime) -> bool:
    return now.weekday() < 5 and OFFICE_START <= now.time() <= OFFICE_END


def fetch_tags() -> list[tuple[int, str, str]]:
    out = subprocess.run(
        ["git", "ls-remote", "--tags", "--refs", REPO_URL],
        check=True, capture_output=True, text=True,
    ).stdout
    tags = []
    for line in out.splitlines():
        name = line.split("refs/tags/", 1)[-1]
        m = TAG_RE.match(name)
        if m:
            tags.append((int(m["build"]), m["version"], name))
    if not tags:
        sys.exit("Keine Tags gefunden, Format geändert?")
    return sorted(tags)


def send_telegram(text: str) -> None:
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    data = urllib.parse.urlencode({
        "chat_id": os.environ["TELEGRAM_CHAT_ID"],
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": "true",
    }).encode()
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        with urllib.request.urlopen(url, data=data, timeout=30) as resp:
            json.load(resp)
    except urllib.error.HTTPError as e:
        detail = json.load(e).get("description", e.reason)
        sys.exit(f"Telegram hat die Nachricht abgelehnt ({e.code}): {detail}")


def main() -> None:
    force = os.environ.get("FORCE") == "true"
    now = datetime.now(TZ)
    if not force and not in_office_hours(now):
        print(f"{now:%a %H:%M} ausserhalb der Bürozeiten, nichts zu tun.")
        return

    tags = fetch_tags()
    latest_build, latest_version, latest_tag = tags[-1]

    if not STATE_FILE.exists():
        send_telegram(
            "✅ Threema-iOS-Überwachung aktiv.\n"
            f"Aktuelle Version: <b>{latest_version}</b> (Build {latest_build})"
        )
    else:
        last_build = int(STATE_FILE.read_text().strip())
        new = [t for t in tags if t[0] > last_build]
        if not new:
            print(f"Keine neue Version (zuletzt Build {last_build}).")
            return
        lines = [
            f"• <b>{v}</b> (Build {b}): <a href=\"{REPO_URL}/releases/tag/{n}\">{n}</a>"
            for b, v, n in new
        ]
        title = "Neue Threema-iOS-Version" if len(new) == 1 else "Neue Threema-iOS-Versionen"
        send_telegram(f"📱 {title}\n" + "\n".join(lines))

    STATE_FILE.parent.mkdir(exist_ok=True)
    STATE_FILE.write_text(f"{latest_build}\n")
    print(f"Gemeldet bis Build {latest_build} ({latest_tag}).")


if __name__ == "__main__":
    main()
