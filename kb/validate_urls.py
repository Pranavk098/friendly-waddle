"""CI-only: verify every KB evidence URL returns 2xx. Performs network I/O.

Usage: uv run python -m kb.validate_urls
"""

from __future__ import annotations

import sys

from kb.build import DEFAULT_FACTS_DIR, check_evidence_urls_live, load_facts


def main() -> int:
    facts = load_facts(DEFAULT_FACTS_DIR)
    errors = check_evidence_urls_live(facts)
    if errors:
        print("Evidence URL check failed:")
        for error in errors:
            print(f"  - {error}")
        return 1
    print(f"All evidence URLs OK ({len(facts)} facts checked).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
