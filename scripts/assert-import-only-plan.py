#!/usr/bin/env python3
"""Exit 0 only for an empty plan or the GitHub Pages cutover plan.

After the import apply, the accepted cutover is exactly:

    10 to add, 0 to change, 1 to destroy

The single destroy must be cloudflare_dns_record.apex (A 46.101.80.89).
MX addresses must not be created, updated, or destroyed. Any other plan fails.
"""

from __future__ import annotations

import re
import sys

IMPORT_PLAN = re.compile(
    r"Plan:\s+(\d+)\s+to import,\s+(\d+)\s+to add,\s+(\d+)\s+to change,\s+(\d+)\s+to destroy\."
)
PLAIN_PLAN = re.compile(
    r"Plan:\s+(\d+)\s+to add,\s+(\d+)\s+to change,\s+(\d+)\s+to destroy\."
)
ACTION_LINE = re.compile(
    r"^\s*#\s+(?P<addr>\S+)\s+will be (?P<action>created|destroyed|updated)\s*$",
    re.MULTILINE,
)
OLD_APEX = "cloudflare_dns_record.apex"
EXPECTED_CREATES = {
    'cloudflare_dns_record.apex_a["185.199.108.153"]',
    'cloudflare_dns_record.apex_a["185.199.109.153"]',
    'cloudflare_dns_record.apex_a["185.199.110.153"]',
    'cloudflare_dns_record.apex_a["185.199.111.153"]',
    'cloudflare_dns_record.apex_aaaa["2606:50c0:8000::153"]',
    'cloudflare_dns_record.apex_aaaa["2606:50c0:8001::153"]',
    'cloudflare_dns_record.apex_aaaa["2606:50c0:8002::153"]',
    'cloudflare_dns_record.apex_aaaa["2606:50c0:8003::153"]',
    "cloudflare_dns_record.www",
    "cloudflare_dns_record.github_pages_challenge",
}


def _summary(text: str) -> tuple[int, int, int, int] | None:
    """Return (import, add, change, destroy) from the last plan summary."""
    imported = IMPORT_PLAN.findall(text)
    if imported:
        return tuple(int(part) for part in imported[-1])
    plain = PLAIN_PLAN.findall(text)
    if plain:
        add, change, destroy = (int(part) for part in plain[-1])
        return (0, add, change, destroy)
    if "No changes." in text:
        return (0, 0, 0, 0)
    return None


def _actions(text: str) -> dict[str, list[str]]:
    found = {"created": [], "destroyed": [], "updated": []}
    for match in ACTION_LINE.finditer(text):
        found[match.group("action")].append(match.group("addr"))
    return found


def evaluate(text: str) -> tuple[bool, str]:
    if "must be replaced" in text or "forces replacement" in text:
        return False, "plan replaces a resource"

    summary = _summary(text)
    if summary is None:
        return False, "plan summary was not recognized; failing closed"

    imported, add, change, destroy = summary
    if (imported, add, change, destroy) == (0, 0, 0, 0):
        return True, "no changes"

    actions = _actions(text)
    mx_hits = [
        address
        for action, addresses in actions.items()
        for address in addresses
        if ".mx_" in address
    ]
    if mx_hits:
        return False, f"plan touches MX records: {', '.join(mx_hits)}"

    if (add, change, destroy) != (10, 0, 1) or imported != 0:
        if destroy == 0 and add == 10:
            return (
                False,
                "import apply has not happened yet, so 46.101.80.89 would be left in Cloudflare; apply the import pull request first",
            )
        return (
            False,
            f"unexpected plan: import={imported} add={add} change={change} destroy={destroy}",
        )

    if actions["destroyed"] != [OLD_APEX]:
        return False, f"destroy set must be only {OLD_APEX}, got {actions['destroyed']}"
    if set(actions["created"]) != EXPECTED_CREATES:
        return False, f"create set mismatch: {sorted(actions['created'])}"
    if actions["updated"]:
        return False, f"plan updates records: {actions['updated']}"
    if "46.101.80.89" not in text:
        return False, "plan does not mention the old apex address 46.101.80.89"
    return True, "10 to add, 0 to change, 1 to destroy (GitHub Pages cutover)"


def main(argv: list[str]) -> int:
    if argv == ["--self-test"]:
        return self_test()
    if len(argv) != 1:
        print("usage: assert-import-only-plan.py PLAN.txt", file=sys.stderr)
        return 2
    text = open(argv[0], encoding="utf-8").read()
    ok, message = evaluate(text)
    print(message)
    return 0 if ok else 1


def _plan(creates: list[str], destroys: list[str], summary: str, extra: str = "") -> str:
    lines = [f"  # {address} will be created" for address in creates]
    lines += [f"  # {address} will be destroyed" for address in destroys]
    body = "\n".join(lines)
    old = "\n          - content = \"46.101.80.89\" -> null\n" if destroys else ""
    return f"{body}{old}{extra}\n{summary}\n"


def self_test() -> int:
    creates = sorted(EXPECTED_CREATES)
    good = _plan(
        creates,
        [OLD_APEX],
        "Plan: 10 to add, 0 to change, 1 to destroy.",
    )
    cases = [
        (good, True),
        ("No changes. Your infrastructure matches the configuration.\n", True),
        (
            _plan(creates, [], "Plan: 10 to add, 0 to change, 0 to destroy."),
            False,
        ),
        (
            _plan(
                creates,
                [OLD_APEX, "cloudflare_dns_record.mx_aspmx"],
                "Plan: 10 to add, 0 to change, 2 to destroy.",
            ),
            False,
        ),
        (
            "  # cloudflare_dns_record.mx_aspmx will be updated in-place\n"
            "Plan: 0 to add, 1 to change, 0 to destroy.\n",
            False,
        ),
    ]
    failed = 0
    for index, (text, expect) in enumerate(cases):
        ok, message = evaluate(text)
        if ok != expect:
            print(f"FAIL case {index}: {ok} {message}", file=sys.stderr)
            failed += 1
    if failed:
        return 1
    print("self-test ok")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
