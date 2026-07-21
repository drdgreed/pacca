"""Tests for the change-manifest validator (pacca.harness.validate_manifest)."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from pacca.harness.validate_manifest import main, validate_manifest

_REPO_ROOT = Path(__file__).resolve().parents[2]
_MANIFEST_DIR = _REPO_ROOT / "harness" / "manifests"
_SCHEMA = _MANIFEST_DIR / "change_manifest.schema.json"
_SHIPPED = sorted(_MANIFEST_DIR.glob("iter-*.json"))


@pytest.mark.parametrize("manifest", _SHIPPED, ids=lambda p: p.name)
def test_shipped_manifest_validates(manifest: Path) -> None:
    """Every iter-N.json that ships in the repo must validate clean."""
    errors = validate_manifest(manifest)
    assert errors == [], "\n".join(errors)


def test_shipped_manifests_exist() -> None:
    # Guard against the glob silently matching nothing (which would vacuously pass above).
    assert len(_SHIPPED) >= 6


@pytest.fixture
def manifest_in_tmp(tmp_path: Path) -> Path:
    """A copy of a real manifest + the schema, in a tmp dir the validator can resolve."""
    shutil.copy(_SCHEMA, tmp_path / _SCHEMA.name)
    dst = tmp_path / "iter-6.json"
    shutil.copy(_SHIPPED[-1], dst)
    return dst


def _load(p: Path) -> dict:
    return json.loads(p.read_text())


def test_missing_required_field_fails(manifest_in_tmp: Path) -> None:
    data = _load(manifest_in_tmp)
    del data["author"]  # required by the schema
    manifest_in_tmp.write_text(json.dumps(data))
    errors = validate_manifest(manifest_in_tmp)
    assert any("author" in e and "required" in e for e in errors), errors


def test_unknown_constraint_level_fails_via_schema(manifest_in_tmp: Path) -> None:
    data = _load(manifest_in_tmp)
    data["changes"][0]["constraint_level"] = "not_a_real_surface"
    manifest_in_tmp.write_text(json.dumps(data))
    errors = validate_manifest(manifest_in_tmp)
    assert any("constraint_level" in e for e in errors), errors


def test_malformed_case_id_fails(manifest_in_tmp: Path) -> None:
    data = _load(manifest_in_tmp)
    data["changes"][0]["predicted_fixes"] = ["GC-7"]  # should be GC-007
    manifest_in_tmp.write_text(json.dumps(data))
    errors = validate_manifest(manifest_in_tmp)
    assert any("malformed case id" in e and "GC-7" in e for e in errors), errors


def test_invalid_json_reports_cleanly(tmp_path: Path) -> None:
    shutil.copy(_SCHEMA, tmp_path / _SCHEMA.name)
    bad = tmp_path / "iter-x.json"
    bad.write_text("{ not valid json ")
    errors = validate_manifest(bad)
    assert len(errors) == 1 and "invalid JSON" in errors[0]


def test_main_all_returns_zero() -> None:
    assert main(["--all", "--dir", str(_MANIFEST_DIR)]) == 0


def test_main_single_bad_returns_one(manifest_in_tmp: Path) -> None:
    data = _load(manifest_in_tmp)
    del data["author"]
    manifest_in_tmp.write_text(json.dumps(data))
    assert main([str(manifest_in_tmp)]) == 1
