import json
from pathlib import Path
from typing import Any

import pytest
import requests
import yaml

from kb.build import build, check_evidence_urls_live, load_facts, validate_facts

SCHEMA_PATH = "kb/schema/fact.schema.json"


def _valid_fact(**overrides: Any) -> dict[str, Any]:
    fact: dict[str, Any] = {
        "id": "sample-fact",
        "category": "experience",
        "claim": "Did a verifiable thing.",
        "evidence": [{"url": "https://example.com/proof", "type": "primary"}],
        "verification": "verified",
        "tags": ["testing"],
    }
    fact.update(overrides)
    return fact


def _schema() -> dict[str, Any]:
    with open(SCHEMA_PATH, encoding="utf-8") as f:
        return json.load(f)  # type: ignore[no-any-return]


def test_validate_facts_flags_missing_required_field() -> None:
    fact = {"id": "x1", "category": "test"}
    errors = validate_facts([fact], _schema())
    assert any("claim" in e for e in errors)


def test_validate_facts_requires_evidence_when_verified() -> None:
    fact = _valid_fact(evidence=[], verification="verified")
    errors = validate_facts([fact], _schema())
    assert any("evidence" in e.lower() for e in errors)


def test_validate_facts_requires_primary_evidence_when_verified() -> None:
    fact = _valid_fact(evidence=[{"url": "https://example.com/x", "type": "self_reported"}])
    errors = validate_facts([fact], _schema())
    assert any("primary" in e.lower() for e in errors)


def test_validate_facts_accepts_valid_verified_fact() -> None:
    fact = _valid_fact()
    errors = validate_facts([fact], _schema())
    assert errors == []


def test_validate_facts_allows_self_reported_without_evidence() -> None:
    fact = _valid_fact(verification="self_reported", evidence=[])
    errors = validate_facts([fact], _schema())
    assert errors == []


def test_validate_facts_detects_duplicate_ids() -> None:
    f1 = _valid_fact(id="dup-id")
    f2 = _valid_fact(id="dup-id")
    errors = validate_facts([f1, f2], _schema())
    assert any("duplicate" in e.lower() and "dup-id" in e for e in errors)


def test_load_facts_reads_yaml_files(tmp_path: Path) -> None:
    facts_dir = tmp_path / "facts"
    facts_dir.mkdir()
    (facts_dir / "sample.yaml").write_text(
        yaml.safe_dump([_valid_fact(id="from-yaml")]), encoding="utf-8"
    )
    facts = load_facts(facts_dir)
    assert len(facts) == 1
    assert facts[0]["id"] == "from-yaml"


def test_build_writes_manifest_and_context(tmp_path: Path) -> None:
    facts_dir = tmp_path / "facts"
    facts_dir.mkdir()
    (facts_dir / "sample.yaml").write_text(
        yaml.safe_dump([_valid_fact()]), encoding="utf-8"
    )
    dist_dir = tmp_path / "dist"

    manifest = build(facts_dir=facts_dir, schema_path=SCHEMA_PATH, dist_dir=dist_dir)

    assert (dist_dir / "manifest.json").exists()
    assert (dist_dir / "context_full.md").exists()
    assert manifest["fact_count"] == 1
    on_disk = json.loads((dist_dir / "manifest.json").read_text(encoding="utf-8"))
    assert on_disk["fact_count"] == 1


def test_build_raises_on_invalid_facts(tmp_path: Path) -> None:
    facts_dir = tmp_path / "facts"
    facts_dir.mkdir()
    (facts_dir / "bad.yaml").write_text(
        yaml.safe_dump([{"id": "bad", "category": "x"}]), encoding="utf-8"
    )
    dist_dir = tmp_path / "dist"

    with pytest.raises(ValueError):
        build(facts_dir=facts_dir, schema_path=SCHEMA_PATH, dist_dir=dist_dir)


class _FakeResponse:
    def __init__(self, status_code: int) -> None:
        self.status_code = status_code


def test_check_evidence_urls_live_reports_non_2xx(monkeypatch: pytest.MonkeyPatch) -> None:
    fact = _valid_fact(evidence=[{"url": "https://example.com/dead", "type": "primary"}])

    def fake_get(url: str, timeout: float) -> _FakeResponse:
        return _FakeResponse(404)

    monkeypatch.setattr("kb.build.requests.get", fake_get)

    errors = check_evidence_urls_live([fact])
    assert any("404" in e and "dead" in e for e in errors)


def test_check_evidence_urls_live_passes_on_2xx(monkeypatch: pytest.MonkeyPatch) -> None:
    fact = _valid_fact(evidence=[{"url": "https://example.com/alive", "type": "primary"}])

    def fake_get(url: str, timeout: float) -> _FakeResponse:
        return _FakeResponse(200)

    monkeypatch.setattr("kb.build.requests.get", fake_get)

    errors = check_evidence_urls_live([fact])
    assert errors == []


def test_check_evidence_urls_live_reports_connection_error_without_crashing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fact = _valid_fact(
        evidence=[{"url": "https://unresolvable.example.invalid/x", "type": "primary"}]
    )

    def fake_get(url: str, timeout: float) -> _FakeResponse:
        raise requests.exceptions.ConnectionError("Failed to resolve host")

    monkeypatch.setattr("kb.build.requests.get", fake_get)

    errors = check_evidence_urls_live([fact])
    assert any("unresolvable.example.invalid" in e for e in errors)


def test_check_evidence_urls_live_skips_in_progress_facts(monkeypatch: pytest.MonkeyPatch) -> None:
    fact = _valid_fact(
        verification="in_progress",
        evidence=[{"url": "https://not-yet-live.example.invalid/x", "type": "self_reported"}],
    )

    def fake_get(url: str, timeout: float) -> _FakeResponse:
        raise requests.exceptions.ConnectionError("should never be called")

    monkeypatch.setattr("kb.build.requests.get", fake_get)

    errors = check_evidence_urls_live([fact])
    assert errors == []
