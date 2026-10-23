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

# MX rows still imported from the 2026-10-23 API capture. comment is null.
# priority None means the API field must be absent or JSON null.
IMPORTED = [
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

# GitHub Pages records created by Terraform. Ids are assigned on apply.
# Addresses match the docs checked on 2026-10-23. DNS only, TTL automatic.
CREATED = [
    {
        "address": 'cloudflare_dns_record.apex_a["185.199.108.153"]',
        "type": "A",
        "name": "jarvis.gg",
        "content": "185.199.108.153",
    },
    {
        "address": 'cloudflare_dns_record.apex_a["185.199.109.153"]',
        "type": "A",
        "name": "jarvis.gg",
        "content": "185.199.109.153",
    },
    {
        "address": 'cloudflare_dns_record.apex_a["185.199.110.153"]',
        "type": "A",
        "name": "jarvis.gg",
        "content": "185.199.110.153",
    },
    {
        "address": 'cloudflare_dns_record.apex_a["185.199.111.153"]',
        "type": "A",
        "name": "jarvis.gg",
        "content": "185.199.111.153",
    },
    {
        "address": 'cloudflare_dns_record.apex_aaaa["2606:50c0:8000::153"]',
        "type": "AAAA",
        "name": "jarvis.gg",
        "content": "2606:50c0:8000::153",
    },
    {
        "address": 'cloudflare_dns_record.apex_aaaa["2606:50c0:8001::153"]',
        "type": "AAAA",
        "name": "jarvis.gg",
        "content": "2606:50c0:8001::153",
    },
    {
        "address": 'cloudflare_dns_record.apex_aaaa["2606:50c0:8002::153"]',
        "type": "AAAA",
        "name": "jarvis.gg",
        "content": "2606:50c0:8002::153",
    },
    {
        "address": 'cloudflare_dns_record.apex_aaaa["2606:50c0:8003::153"]',
        "type": "AAAA",
        "name": "jarvis.gg",
        "content": "2606:50c0:8003::153",
    },
    {
        "address": "cloudflare_dns_record.www",
        "type": "CNAME",
        "name": "www.jarvis.gg",
        "content": "jarvvski.github.io",
    },
    {
        "address": "cloudflare_dns_record.github_pages_challenge",
        "type": "TXT",
        "name": "_github-pages-challenge-jarvvski.jarvis.gg",
        "content": "8246776e59edf2bb27a58013c4317d",
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


def _check(address: str, live: dict, expected: dict) -> list[str]:
    checks = {
        "type": (live.get("type"), expected["type"]),
        "name": (live.get("name"), expected["name"]),
        "content": (live.get("content"), expected["content"]),
        "ttl": (live.get("ttl"), expected.get("ttl", 1)),
        "proxied": (live.get("proxied"), expected.get("proxied", False)),
        "comment": (live.get("comment"), None),
        "priority": (_priority(live), expected.get("priority")),
    }
    problems = []
    for field, (actual, wanted) in checks.items():
        if actual != wanted:
            problems.append(f"{address} {field}: api={actual!r} config={wanted!r}")
    return problems


def compare(records: list[dict]) -> list[str]:
    """Return human-readable drift lines. Empty means the managed set matches."""
    by_id = {record.get("id"): record for record in records}
    problems: list[str] = []
    consumed: set[str] = set()

    for item in IMPORTED:
        live = by_id.get(item["id"])
        if live is None:
            problems.append(f"missing {item['address']} id={item['id']}")
            continue
        consumed.add(item["id"])
        problems.extend(_check(item["address"], live, item))

    for item in CREATED:
        matches = [
            record
            for record in records
            if record.get("type") == item["type"]
            and record.get("name") == item["name"]
            and record.get("content") == item["content"]
            and record.get("id") not in consumed
        ]
        if not matches:
            problems.append(
                f"missing {item['address']} {item['type']} {item['name']} {item['content']}"
            )
            continue
        live = matches[0]
        consumed.add(live["id"])
        problems.extend(_check(item["address"], live, item))

    for record in records:
        if record.get("id") in consumed or record.get("type") == "NS":
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
    print("import blocks for the MX records:")
    print()
    for item in IMPORTED:
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
    print("After the GitHub Pages apply, terraform plan should report no changes.")
    return 0


def _live_from(item: dict, record_id: str) -> dict:
    record = {
        "id": record_id,
        "type": item["type"],
        "name": item["name"],
        "content": item["content"],
        "ttl": item.get("ttl", 1),
        "proxied": item.get("proxied", False),
        "comment": None,
    }
    if item.get("priority") is not None:
        record["priority"] = item["priority"]
    return record


def self_test() -> int:
    sample = [_live_from(item, item["id"]) for item in IMPORTED]
    sample += [_live_from(item, f"created-{index}") for index, item in enumerate(CREATED)]
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
        print("\n".join(compare(sample)), file=sys.stderr)
        return 1
    drifted = json.loads(json.dumps(sample))
    drifted[0]["priority"] = 99
    if not compare(drifted):
        print("self-test: priority drift was ignored", file=sys.stderr)
        return 1
    extra = json.loads(json.dumps(sample))
    extra.append(
        {
            "id": "old-apex",
            "type": "A",
            "name": "jarvis.gg",
            "content": "46.101.80.89",
            "ttl": 1,
            "proxied": True,
            "comment": None,
        }
    )
    if not any("46.101.80.89" in line for line in compare(extra)):
        print("self-test: old apex was ignored", file=sys.stderr)
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
