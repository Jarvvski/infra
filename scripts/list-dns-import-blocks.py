#!/usr/bin/env python3
"""List jarvis.gg DNS records and print Terraform import blocks.

Reads the live zone from the Cloudflare API and compares it to the records
committed in cloudflare/jarvis-gg. Record ids and the zone id are public.
The API token is read from CLOUDFLARE_API_TOKEN and is never printed.

Usage:
  CLOUDFLARE_API_TOKEN=... ./scripts/list-dns-import-blocks.sh
  ./scripts/list-dns-import-blocks.py --self-test
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request

ZONE_ID = os.environ.get("ZONE_ID", "25a69e647ecf731fb8268a02b55e8afa")

# Values captured from the Cloudflare API on 2026-10-23. comment is null.
# priority None means the API field must be absent or JSON null (the A record).
EXPECTED = [
    {
        "address": "cloudflare_dns_record.apex",
        "id": "b73d8cea608feae5a5179334ba81ba16",
        "type": "A",
        "name": "jarvis.gg",
        "content": "46.101.80.89",
        "priority": None,
        "ttl": 1,
        "proxied": True,
    },
    {
        "address": "cloudflare_dns_record.mx_aspmx",
        "id": "3a83636116fbdd503cd53b4dd308e0f0",
        "type": "MX",
        "name": "jarvis.gg",
        "content": "aspmx.l.google.com",
        "priority": 1,
        "ttl": 1,
        "proxied": False,
    },
    {
        "address": "cloudflare_dns_record.mx_alt1",
        "id": "0a6b4a8ba79f45cb079af04ec0dd575c",
        "type": "MX",
        "name": "jarvis.gg",
        "content": "alt1.aspmx.l.google.com",
        "priority": 5,
        "ttl": 1,
        "proxied": False,
    },
    {
        "address": "cloudflare_dns_record.mx_alt2",
        "id": "9c425b9a0f8cebfe221a259e3a78bc79",
        "type": "MX",
        "name": "jarvis.gg",
        "content": "alt2.aspmx.l.google.com",
        "priority": 5,
        "ttl": 1,
        "proxied": False,
    },
    {
        "address": "cloudflare_dns_record.mx_aspmx2",
        "id": "9f71afd265c8831e0fbe51092c6f185d",
        "type": "MX",
        "name": "jarvis.gg",
        "content": "aspmx2.googlemail.com",
        "priority": 10,
        "ttl": 1,
        "proxied": False,
    },
    {
        "address": "cloudflare_dns_record.mx_aspmx3",
        "id": "47b70150a5771195aa9f60d1f39410d5",
        "type": "MX",
        "name": "jarvis.gg",
        "content": "aspmx3.googlemail.com",
        "priority": 10,
        "ttl": 1,
        "proxied": False,
    },
]


def fetch_records(zone_id: str, token: str) -> list[dict]:
    records: list[dict] = []
    page = 1
    while True:
        url = (
            "https://api.cloudflare.com/client/v4/zones/"
            f"{zone_id}/dns_records?per_page=100&page={page}"
        )
        request = urllib.request.Request(
            url,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                payload = json.load(response)
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise SystemExit(f"Cloudflare API HTTP {exc.code}: {body}") from exc
        if not payload.get("success"):
            raise SystemExit(f"Cloudflare API error: {payload.get('errors')}")
        records.extend(payload.get("result") or [])
        info = payload.get("result_info") or {}
        total_pages = int(info.get("total_pages") or 1)
        if page >= total_pages:
            return records
        page += 1


def _priority(record: dict):
    if "priority" not in record or record["priority"] is None:
        return None
    return record["priority"]


def compare(records: list[dict]) -> list[str]:
    """Return human-readable drift lines. Empty means the managed set matches."""
    by_id = {record.get("id"): record for record in records}
    problems: list[str] = []
    expected_ids = {item["id"] for item in EXPECTED}

    for item in EXPECTED:
        live = by_id.get(item["id"])
        if live is None:
            problems.append(f"missing {item['address']} id={item['id']}")
            continue
        checks = {
            "type": (live.get("type"), item["type"]),
            "name": (live.get("name"), item["name"]),
            "content": (live.get("content"), item["content"]),
            "ttl": (live.get("ttl"), item["ttl"]),
            "proxied": (live.get("proxied"), item["proxied"]),
            "comment": (live.get("comment"), None),
            "priority": (_priority(live), item["priority"]),
        }
        for field, (actual, expected) in checks.items():
            if actual != expected:
                problems.append(
                    f"{item['address']} {field}: api={actual!r} config={expected!r}"
                )

    for record in records:
        if record.get("id") in expected_ids:
            continue
        if record.get("type") == "NS":
            continue
        problems.append(
            "unmanaged {type} {name} content={content!r} id={id} "
            "(only NS records are intentionally outside Terraform)".format(
                type=record.get("type"),
                name=record.get("name"),
                content=record.get("content"),
                id=record.get("id"),
            )
        )
    return problems


def print_report(records: list[dict]) -> int:
    print(f"zone {ZONE_ID}: {len(records)} record(s)")
    print()
    for record in records:
        print(
            "{id} {type} {name} content={content} priority={priority} "
            "ttl={ttl} proxied={proxied} comment={comment}".format(
                id=record.get("id"),
                type=record.get("type"),
                name=record.get("name"),
                content=record.get("content"),
                priority=record.get("priority"),
                ttl=record.get("ttl"),
                proxied=record.get("proxied"),
                comment=record.get("comment"),
            )
        )

    print()
    print("import blocks for the managed records:")
    print()
    for item in EXPECTED:
        print("import {")
        print(f"  to = {item['address']}")
        print(f'  id = "{ZONE_ID}/{item["id"]}"')
        print("}")
        print()

    ns = [record for record in records if record.get("type") == "NS"]
    if ns:
        print("NS records are Cloudflare nameservers and stay unmanaged:")
        for record in ns:
            print(f"  {record.get('id')} {record.get('name')} {record.get('content')}")
        print()

    problems = compare(records)
    if problems:
        print("DRIFT against cloudflare/jarvis-gg (do not apply):")
        for line in problems:
            print(f"  {line}")
        return 1

    print("Managed records match the Terraform configuration.")
    print("A terraform plan should be: 6 to import, 0 to add, 0 to change, 0 to destroy.")
    print("After that import is applied, later plans should report no changes.")
    return 0


def self_test() -> int:
    sample = []
    for item in EXPECTED:
        record = {
            "id": item["id"],
            "type": item["type"],
            "name": item["name"],
            "content": item["content"],
            "ttl": item["ttl"],
            "proxied": item["proxied"],
            "comment": None,
        }
        if item["priority"] is not None:
            record["priority"] = item["priority"]
        sample.append(record)
    sample.append(
        {
            "id": "ns1",
            "type": "NS",
            "name": "jarvis.gg",
            "content": "ns1.cloudflare.com",
            "ttl": 86400,
            "proxied": False,
            "comment": None,
        }
    )
    if compare(sample):
        print("self-test: matching fixture reported drift", file=sys.stderr)
        return 1
    drifted = json.loads(json.dumps(sample))
    drifted[1]["priority"] = 99
    if not compare(drifted):
        print("self-test: priority drift was ignored", file=sys.stderr)
        return 1
    extra = json.loads(json.dumps(sample))
    extra.append(
        {
            "id": "txt1",
            "type": "TXT",
            "name": "jarvis.gg",
            "content": "v=spf1",
            "ttl": 1,
            "proxied": False,
            "comment": None,
        }
    )
    if not any("unmanaged TXT" in line for line in compare(extra)):
        print("self-test: extra TXT was ignored", file=sys.stderr)
        return 1
    print("self-test ok")
    return 0


def main(argv: list[str]) -> int:
    if "--self-test" in argv:
        return self_test()
    token = os.environ.get("CLOUDFLARE_API_TOKEN", "")
    if not token.strip():
        print("CLOUDFLARE_API_TOKEN is required", file=sys.stderr)
        return 1
    records = fetch_records(ZONE_ID, token)
    return print_report(records)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
