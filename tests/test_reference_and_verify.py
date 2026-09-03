import copy
import csv
import hashlib
from pathlib import Path
import shutil
import subprocess

import pytest

from reservoir_market_backtest.artifacts import ArtifactHashMismatch
from reservoir_market_backtest.reference import (
    ReferenceValidationError,
    load_json,
    validate_claim_ledger,
    validate_reference,
)
from reservoir_market_backtest.release_manifest import (
    MANIFEST_COLUMNS,
    ReleaseManifestError,
    verify_release_manifest,
)
from reservoir_market_backtest.verify import build_verification_report, scan_public_boundary


ROOT = Path(__file__).resolve().parents[1]


def test_public_reference_and_claims_are_self_consistent() -> None:
    reference = load_json(ROOT / "results" / "reference_results.json")
    ledger = load_json(ROOT / "results" / "claim_ledger.json")
    assert "calendar_and_session_calmar_conventions" in validate_reference(reference)
    checked_claims = validate_claim_ledger(ledger)
    assert "validated_alpha_or_future_performance" in checked_claims
    assert "holdout_raw_accuracy" in checked_claims
    assert reference["historical_holdout"]["portfolio_metrics"]["calendar_calmar_ratio"] == pytest.approx(
        1.3299281129269813
    )
    assert reference["historical_holdout"]["portfolio_metrics"]["session_calmar_ratio"] == pytest.approx(
        1.3384864941249204
    )


def test_reference_rejects_promotional_claim_mutation() -> None:
    reference = load_json(ROOT / "results" / "reference_results.json")
    changed = copy.deepcopy(reference)
    changed["historical_holdout"]["portfolio_metrics"]["final_equity"] = 2.0
    with pytest.raises(ReferenceValidationError):
        validate_reference(changed)


def test_claim_ledger_keeps_descriptive_scope_explicit() -> None:
    ledger = load_json(ROOT / "results" / "claim_ledger.json")
    by_id = {record["id"]: record for record in ledger["claims"]}
    assert "55.24" in by_id["holdout_raw_accuracy"]["claim"]
    assert "628 sessions" in by_id["holdout_raw_accuracy"]["conditions"]
    assert by_id["validated_alpha_or_future_performance"]["status"] == "not_claimed"
    assert by_id["public_end_to_end_rerun"]["status"] == "not_available"


def test_default_verification_uses_only_public_aggregates() -> None:
    report = build_verification_report(repository_root=ROOT)
    assert report["status"] == "pass"
    assert report["verification_level"] == "public_safe_aggregate_reference"
    assert report["private_evidence"] == {
        "holdout_series": "not supplied",
    }


def test_official_private_path_is_hash_gated_before_parse(tmp_path) -> None:
    malformed = tmp_path / "not-an-npz.npz"
    malformed.write_bytes(b"this is not the retained artifact")
    with pytest.raises(ArtifactHashMismatch):
        build_verification_report(repository_root=ROOT, holdout_series=malformed)


def test_release_boundary_rejects_private_array(tmp_path) -> None:
    (tmp_path / "results").mkdir()
    (tmp_path / "results" / "private.npz").write_bytes(b"private")
    with pytest.raises(ValueError, match="release-tree violations"):
        scan_public_boundary(tmp_path)


@pytest.mark.parametrize(
    "relative",
    [
        ".pytest_cache/v/cache/nodeids",
        "src/pkg/__pycache__/x.pyc",
        "src/pkg.egg-info/PKG-INFO",
        "build/output.txt",
    ],
)
def test_release_boundary_ignores_untracked_runtime_debris(
    tmp_path, relative: str
) -> None:
    path = tmp_path / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("generated", encoding="utf-8")
    assert "runtime_debris_excluded_by_exact_manifest" in scan_public_boundary(tmp_path)


@pytest.mark.parametrize(
    "relative",
    [
        "evidence/private.npz",
        "native/runner.so",
        "archive/source.tar.gz",
        "payload.zip",
    ],
)
def test_release_boundary_rejects_sensitive_binary_or_archive(
    tmp_path, relative: str
) -> None:
    path = tmp_path / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"not public")
    with pytest.raises(ReleaseManifestError, match="release-tree violations"):
        scan_public_boundary(tmp_path)


def test_release_boundary_rejects_symlink_before_following_it(tmp_path) -> None:
    private = tmp_path.parent / "private.txt"
    private.write_text("secret", encoding="utf-8")
    (tmp_path / "apparently-safe.txt").symlink_to(private)
    with pytest.raises(ReleaseManifestError, match="symlink"):
        scan_public_boundary(tmp_path)


def _write_manifest(root: Path, paths: list[str]) -> None:
    destination = root / "evidence" / "RELEASE_MANIFEST.csv"
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(MANIFEST_COLUMNS)
        for relative in sorted(paths):
            payload = (root / relative).read_bytes()
            writer.writerow(
                (relative, len(payload), hashlib.sha256(payload).hexdigest())
            )


def test_release_manifest_is_exact_and_hash_gated(tmp_path) -> None:
    (tmp_path / "README.md").write_text("verified\n", encoding="utf-8")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "method.py").write_text("VALUE = 1\n", encoding="utf-8")
    _write_manifest(tmp_path, ["README.md", "src/method.py"])
    assert verify_release_manifest(tmp_path)["status"] == "exact_allowlist_match"
    (tmp_path / "src" / "method.py").write_text("VALUE = 2\n", encoding="utf-8")
    with pytest.raises(ReleaseManifestError, match="changed"):
        verify_release_manifest(tmp_path)


def test_manifest_cannot_allowlist_generated_debris(tmp_path) -> None:
    generated = tmp_path / "src" / "pkg.egg-info" / "PKG-INFO"
    generated.parent.mkdir(parents=True)
    generated.write_text("generated", encoding="utf-8")
    _write_manifest(tmp_path, ["src/pkg.egg-info/PKG-INFO"])
    with pytest.raises(ReleaseManifestError, match="forbidden file"):
        verify_release_manifest(tmp_path)


@pytest.mark.skipif(shutil.which("git") is None, reason="Git is not installed")
def test_manifest_rejects_tracked_file_hidden_in_ignored_directory(tmp_path) -> None:
    (tmp_path / "README.md").write_text("verified\n", encoding="utf-8")
    hidden = tmp_path / "build" / "private-source.txt"
    hidden.parent.mkdir()
    hidden.write_text("must not ship\n", encoding="utf-8")
    _write_manifest(tmp_path, ["README.md"])
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    subprocess.run(
        [
            "git",
            "-C",
            str(tmp_path),
            "add",
            "-f",
            "README.md",
            "evidence/RELEASE_MANIFEST.csv",
            "build/private-source.txt",
        ],
        check=True,
    )
    with pytest.raises(ReleaseManifestError, match="unmanifested_tracked"):
        verify_release_manifest(tmp_path)
