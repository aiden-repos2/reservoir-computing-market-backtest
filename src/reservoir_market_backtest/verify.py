"""Public-safe and optional private-evidence verification orchestration."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .artifacts import identify_private_artifact, load_artifact_manifest
from .private_analysis import analyze_holdout_series
from .reference import (
    compare_holdout_analysis,
    load_json,
    validate_claim_ledger,
    validate_reference,
)
from .release_manifest import (
    MANIFEST_RELATIVE_PATH,
    ReleaseFile,
    build_release_records,
    load_release_manifest,
    validate_manifest_paths,
    verify_release_manifest,
)


def find_repository_root(start: str | Path | None = None) -> Path:
    current = Path(start or Path.cwd()).resolve()
    if current.is_file():
        current = current.parent
    for candidate in (current, *current.parents):
        if (candidate / "results" / "reference_results.json").is_file():
            return candidate
    package_candidate = Path(__file__).resolve().parents[2]
    if (package_candidate / "results" / "reference_results.json").is_file():
        return package_candidate
    raise FileNotFoundError("could not locate results/reference_results.json")


def scan_public_boundary(
    root: str | Path,
    *,
    release_paths: list[str] | None = None,
) -> list[str]:
    """Validate public files while tolerating ignored local runtime debris.

    Without ``release_paths`` this performs a conservative tree scan.  The
    release verifier passes the exact manifest allowlist, which also ensures
    that ignored install/test debris cannot accidentally become published.
    """

    repo = Path(root)
    if release_paths is None:
        # This traversal rejects sensitive formats, archives, compiled objects,
        # and symlinks.  Known untracked caches are deliberately skipped.
        build_release_records(repo)
    else:
        validate_manifest_paths(
            # Only the path is relevant to this boundary pass.
            ReleaseFile(path=value, size_bytes=0, sha256="0" * 64)
            for value in release_paths
        )
    return [
        "no_private_array_formats",
        "no_raw_or_feature_directories",
        "no_compiled_objects_or_nested_archives",
        "no_symlinks",
        "runtime_debris_excluded_by_exact_manifest",
    ]


def build_verification_report(
    *,
    repository_root: str | Path | None = None,
    holdout_series: str | Path | None = None,
) -> dict[str, Any]:
    root = find_repository_root(repository_root)
    reference = load_json(root / "results" / "reference_results.json")
    ledger = load_json(root / "results" / "claim_ledger.json")
    manifest = load_artifact_manifest(root / "evidence" / "private_artifact_hashes.json")
    release_manifest_path = root / Path(MANIFEST_RELATIVE_PATH.as_posix())
    release_records = load_release_manifest(release_manifest_path)

    report: dict[str, Any] = {
        "status": "pass",
        "verification_level": "public_safe_aggregate_reference",
        "public_checks": {
            "reference": validate_reference(reference),
            "claim_ledger": validate_claim_ledger(ledger),
            "release_boundary": scan_public_boundary(
                root, release_paths=[record.path for record in release_records]
            ),
            "release_manifest": verify_release_manifest(root),
        },
        "headline": {
            "calendar_calmar_ratio": reference["historical_holdout"]["portfolio_metrics"][
                "calendar_calmar_ratio"
            ],
            "session_calmar_ratio": reference["historical_holdout"]["portfolio_metrics"][
                "session_calmar_ratio"
            ],
            "concise_calmar": "approximately 1.33",
            "scope": "descriptive historical simulation",
        },
        "private_evidence": {
            "holdout_series": "not supplied",
        },
    }

    if holdout_series is not None:
        identity, verified = identify_private_artifact(
            holdout_series,
            manifest,
            ("holdout_series_original", "holdout_series_minimized"),
        )
        analysis = analyze_holdout_series(holdout_series)
        compare_holdout_analysis(analysis, reference)
        report["private_evidence"]["holdout_series"] = {
            "identity": verified,
            "semantic_profile": manifest["private_artifacts"][identity.artifact_id][
                "semantic_profile"
            ],
            "analysis": analysis,
            "comparison": "matches aggregate reference",
        }
        report["verification_level"] = "exact_metric_replay"

    return report


def format_verification_report(report: dict[str, Any]) -> str:
    headline = report["headline"]
    private = report["private_evidence"]
    lines = [
        "PASS: reservoir-computing market backtest verification",
        f"Verification level: {report['verification_level']}",
        (
            "Historical Calmar: "
            f"{headline['calendar_calmar_ratio']:.6f} (elapsed calendar time); "
            f"{headline['session_calmar_ratio']:.6f} (252-session convention)"
        ),
        "Concise historical value: approximately 1.33",
        "Scope: descriptive historical simulation; no prospective performance claim.",
    ]
    for label in ("holdout_series",):
        value = private[label]
        if isinstance(value, dict):
            lines.append(
                f"Private {label}: {value['identity']['artifact_id']} verified and matched"
            )
        else:
            lines.append(f"Private {label}: {value} (optional; no automatic download)")
    return "\n".join(lines)
