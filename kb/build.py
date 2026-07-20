"""Compile kb/facts/*.yaml into kb/dist/ artifacts.

Usage: uv run python kb/build.py
"""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import requests
import yaml
from jsonschema import Draft202012Validator

DEFAULT_FACTS_DIR = Path("kb/facts")
DEFAULT_SCHEMA_PATH = Path("kb/schema/fact.schema.json")
DEFAULT_DIST_DIR = Path("kb/dist")


def load_facts(facts_dir: Path) -> list[dict[str, Any]]:
    """Load and flatten every fact list from *.yaml files in facts_dir."""
    facts: list[dict[str, Any]] = []
    for yaml_file in sorted(Path(facts_dir).glob("*.yaml")):
        content: list[dict[str, Any]] = (
            yaml.safe_load(yaml_file.read_text(encoding="utf-8")) or []
        )
        facts.extend(content)
    return facts


def validate_facts(facts: list[dict[str, Any]], schema: dict[str, Any]) -> list[str]:
    """Return a list of human-readable validation errors (empty = valid)."""
    errors: list[str] = []
    validator = Draft202012Validator(schema)
    seen_ids: set[str] = set()

    for fact in facts:
        fact_id = fact.get("id", "<missing id>")

        for error in validator.iter_errors(fact):  # pyright: ignore[reportUnknownMemberType]
            errors.append(f"fact '{fact_id}': {error.message}")

        if fact.get("verification") == "verified":
            evidence = fact.get("evidence", [])
            if not evidence:
                errors.append(
                    f"fact '{fact_id}': verified facts must include at least one evidence entry"
                )
            elif not any(e.get("type") == "primary" for e in evidence):
                errors.append(
                    f"fact '{fact_id}': verified facts must include at least one "
                    "evidence entry with type 'primary'"
                )

        if fact_id in seen_ids:
            errors.append(f"duplicate fact id: {fact_id}")
        seen_ids.add(fact_id)

    return errors


def check_evidence_urls_live(facts: list[dict[str, Any]]) -> list[str]:
    """Fetch every evidence URL and report non-2xx responses. Network I/O — CI only.

    Skips facts marked verification: in_progress — their evidence isn't claimed as
    checkable yet, so an unreachable URL there isn't a real finding.
    """
    errors: list[str] = []
    for fact in facts:
        if fact.get("verification") == "in_progress":
            continue
        for evidence in fact.get("evidence", []):
            url = evidence["url"]
            try:
                response = requests.get(url, timeout=10)
            except requests.exceptions.RequestException as exc:
                errors.append(f"evidence URL unreachable: {url} ({exc})")
                continue
            if not (200 <= response.status_code < 300):
                errors.append(f"evidence URL returned {response.status_code}: {url}")
    return errors


def render_context_markdown(facts: list[dict[str, Any]]) -> str:
    by_category: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for fact in facts:
        by_category[fact.get("category", "uncategorized")].append(fact)

    lines = ["# Compiled Knowledge Base", ""]
    for category in sorted(by_category):
        lines.append(f"## {category}")
        lines.append("")
        for fact in by_category[category]:
            urls = ", ".join(e["url"] for e in fact.get("evidence", []))
            suffix = f" [evidence: {urls}]" if urls else ""
            lines.append(f"- **{fact['id']}**: {fact['claim']}{suffix}")
        lines.append("")
    return "\n".join(lines)


def build(
    facts_dir: Path = DEFAULT_FACTS_DIR,
    schema_path: Path | str = DEFAULT_SCHEMA_PATH,
    dist_dir: Path = DEFAULT_DIST_DIR,
) -> dict[str, Any]:
    schema = json.loads(Path(schema_path).read_text(encoding="utf-8"))
    facts = load_facts(facts_dir)

    errors = validate_facts(facts, schema)
    if errors:
        raise ValueError("KB validation failed:\n" + "\n".join(f"  - {e}" for e in errors))

    dist_dir = Path(dist_dir)
    dist_dir.mkdir(parents=True, exist_ok=True)

    manifest = {
        "fact_count": len(facts),
        "built_at": datetime.now(UTC).isoformat(),
    }
    (dist_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    (dist_dir / "context_full.md").write_text(
        render_context_markdown(facts), encoding="utf-8"
    )

    return manifest


if __name__ == "__main__":
    result = build()
    print(f"Built KB: {result['fact_count']} facts -> {DEFAULT_DIST_DIR}/")
