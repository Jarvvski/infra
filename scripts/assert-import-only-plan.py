#!/usr/bin/env python3
"""Exit 0 when a terraform plan does not add, change, or destroy anything.

Import-only plans are allowed. This is the import pull request's gate.
The GitHub Pages cutover adds and destroys records, so CI runs this only when
the repository variable TF_PLAN_IMPORT_ONLY is true.
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
FORBIDDEN = (
    "will be destroyed",
    "will be created",
    "will be updated",
    "must be replaced",
    "forces replacement",
)


def evaluate(text: str) -> tuple[bool, str]:
    for phrase in FORBIDDEN:
        if phrase in text:
            return False, f"plan contains {phrase!r}"

    import_summaries = IMPORT_PLAN.findall(text)
    if import_summaries:
        imported, add, change, destroy = (int(part) for part in import_summaries[-1])
        if add == 0 and change == 0 and destroy == 0:
            return True, f"{imported} to import, 0 to add, 0 to change, 0 to destroy"
        return (
            False,
            f"plan would change DNS: import={imported} add={add} change={change} destroy={destroy}",
        )

    plain_summaries = PLAIN_PLAN.findall(text)
    if plain_summaries:
        add, change, destroy = (int(part) for part in plain_summaries[-1])
        if add == 0 and change == 0 and destroy == 0:
            return True, "0 to add, 0 to change, 0 to destroy"
        return False, f"plan would change DNS: add={add} change={change} destroy={destroy}"

    if "No changes." in text:
        return True, "no changes"

    return False, "plan summary was not recognized; failing closed"


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


def self_test() -> int:
    cases = [
        (
            "  # cloudflare_dns_record.mx_aspmx will be imported\n"
            "Plan: 5 to import, 0 to add, 0 to change, 0 to destroy.\n",
            True,
        ),
        ("No changes. Your infrastructure matches the configuration.\n", True),
        ("Plan: 0 to add, 0 to change, 0 to destroy.\n", True),
        (
            "  # cloudflare_dns_record.www will be created\n"
            "  # cloudflare_dns_record.apex will be destroyed\n"
            "Plan: 10 to add, 0 to change, 1 to destroy.\n",
            False,
        ),
        (
            "  # cloudflare_dns_record.mx_aspmx will be updated in-place\n"
            "Plan: 0 to add, 1 to change, 0 to destroy.\n",
            False,
        ),
        ("Error: no credentials\n", False),
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
