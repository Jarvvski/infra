#!/usr/bin/env python3
"""Exit 0 when a terraform plan does not add, change, or destroy anything.

Import-only plans are allowed. Those adopt the existing jarvis.gg records
and leave Cloudflare unchanged. Any other action fails the check.
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
    if len(argv) != 1:
        print("usage: assert-import-only-plan.py PLAN.txt", file=sys.stderr)
        return 2
    text = open(argv[0], encoding="utf-8").read()
    ok, message = evaluate(text)
    print(message)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
