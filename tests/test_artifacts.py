import hashlib

import numpy as np
import pytest

from reservoir_market_backtest.artifacts import (
    ArtifactHashMismatch,
    ArtifactIdentity,
    identify_private_artifact,
    verify_private_artifact,
)
from reservoir_market_backtest.private_analysis import analyze_holdout_series
from reservoir_market_backtest.schema import SYMBOLS


def identity_for(path, artifact_id="fixture") -> ArtifactIdentity:
    payload = path.read_bytes()
    return ArtifactIdentity(
        artifact_id=artifact_id,
        logical_path=f"fixtures/{path.name}",
        sha256=hashlib.sha256(payload).hexdigest(),
        size_bytes=len(payload),
        classification="synthetic_test_fixture",
    )


def test_hash_gate_accepts_exact_bytes_and_rejects_changes(tmp_path) -> None:
    path = tmp_path / "artifact.bin"
    path.write_bytes(b"frozen evidence")
    identity = identity_for(path)
    assert verify_private_artifact(path, identity)["status"] == "verified_before_parse"
    path.write_bytes(b"changed evidence")
    with pytest.raises(ArtifactHashMismatch):
        verify_private_artifact(path, identity)


def test_profile_identifier_fails_closed_on_unknown_hash(tmp_path) -> None:
    path = tmp_path / "artifact.bin"
    path.write_bytes(b"known")
    identity = identity_for(path, "known")
    manifest = {
        "private_artifacts": {
            "known": {
                "logical_path": identity.logical_path,
                "sha256": identity.sha256,
                "size_bytes": identity.size_bytes,
                "classification": identity.classification,
            }
        }
    }
    matched, _ = identify_private_artifact(path, manifest, ("known",))
    assert matched.artifact_id == "known"
    path.write_bytes(b"unknown")
    with pytest.raises(ArtifactHashMismatch):
        identify_private_artifact(path, manifest, ("known",))


def test_synthetic_holdout_npz_reconstructs_common_equal_weight_path(tmp_path) -> None:
    path = tmp_path / "holdout.npz"
    dates = np.array(["2024-01-02", "2024-01-03", "2024-01-04"], dtype="datetime64[ns]").astype(np.int64)
    payload = {}
    for index, symbol in enumerate(SYMBOLS):
        payload[f"ikeda1__{symbol}__dt"] = dates
        payload[f"ikeda1__{symbol}__ret"] = np.array([0.001, -0.002, 0.003]) + index * 1e-5
    np.savez(path, **payload)
    result = analyze_holdout_series(path)
    assert result["n_days"] == 3
    assert result["n_symbols"] == 9
    assert result["first_date"] == "2024-01-02"
    assert result["last_date"] == "2024-01-04"
