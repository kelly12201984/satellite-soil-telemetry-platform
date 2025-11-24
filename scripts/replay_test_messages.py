#!/usr/bin/env python3
"""
Replay captured Globalstar .eml uplink messages into the local API.

Usage:
    python scripts/replay_test_messages.py \
        --dir Test-Messages \
        --url http://localhost:8000/v1/uplink/receive \
        --token <optional-shared-token>

The script looks for XML payloads inside each .eml file (typically inside the
text/plain part), posts them to the uplink endpoint, and prints a summary.
"""
from __future__ import annotations

import argparse
import email
from email.message import Message
import sys
from pathlib import Path
from typing import Optional
from urllib import error, request

DEFAULT_URL = "http://localhost:8000/v1/uplink/receive"


def extract_xml(msg: Message) -> Optional[str]:
    """Return the first XML payload found inside the email message."""
    parts = [msg] if not msg.is_multipart() else list(msg.walk())
    for part in parts:
        content_type = part.get_content_type()
        if content_type not in {"text/plain", "text/xml", "application/xml"}:
            continue
        payload = part.get_payload(decode=True)
        if not payload:
            continue
        charset = part.get_content_charset() or "utf-8"
        try:
            text = payload.decode(charset, errors="ignore").strip()
        except LookupError:
            text = payload.decode("utf-8", errors="ignore").strip()
        start = text.find("<?xml")
        if start != -1:
            return text[start:]
    return None


def post_xml(url: str, xml: str, token: Optional[str]) -> tuple[int, str]:
    data = xml.encode("utf-8")
    headers = {"Content-Type": "application/xml"}
    if token:
        headers["X-Uplink-Token"] = token
    req = request.Request(url, data=data, headers=headers, method="POST")
    try:
        with request.urlopen(req) as resp:
            body = resp.read().decode("utf-8", errors="ignore")
            return resp.status, body
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="ignore")
        return exc.code, body
    except Exception as exc:  # pragma: no cover - troubleshooting helper
        return 0, str(exc)


def main() -> int:
    parser = argparse.ArgumentParser(description="Replay Globalstar .eml messages")
    parser.add_argument("--dir", type=Path, default=Path("Test-Messages"), help="Directory with .eml files")
    parser.add_argument("--url", default=DEFAULT_URL, help="Uplink endpoint URL")
    parser.add_argument("--token", default=None, help="Optional X-Uplink-Token value")
    parser.add_argument("--limit", type=int, default=0, help="Max number of files to replay (0 = all)")
    args = parser.parse_args()

    if not args.dir.exists():
        print(f"❌ Directory not found: {args.dir}")
        return 1

    files = sorted(args.dir.glob("*.eml"))
    if args.limit:
        files = files[: args.limit]

    if not files:
        print(f"⚠️ No .eml files found in {args.dir}")
        return 0

    successes = failures = 0

    print(f"📡 Replaying {len(files)} message(s) to {args.url}")
    for path in files:
        raw = path.read_bytes()
        msg = email.message_from_bytes(raw)
        xml = extract_xml(msg)
        if not xml:
            failures += 1
            print(f"  ✖ {path.name}: no XML payload found")
            continue
        status, body = post_xml(args.url, xml, args.token)
        if 200 <= status < 300:
            successes += 1
            print(f"  ✓ {path.name}: {status} {body.strip()[:120]}")
        else:
            failures += 1
            print(f"  ✖ {path.name}: {status} {body.strip()[:200]}")

    print(f"\n✅ Done. Success: {successes} | Failed: {failures}")
    return 0 if failures == 0 else 2


if __name__ == "__main__":
    sys.exit(main())

