"""Cryptographic identity checks for private, non-redistributed evidence."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import hmac
import json
from pathlib import Path
from typing import Any


class ArtifactVerificationError(ValueError):
    """Base class for private-evidence identity failures."""


class ArtifactHashMismatch(ArtifactVerificationError):
    """Raised before parsing when a private artifact has the wrong digest."""


@dataclass(frozen=True)
class ArtifactIdentity:
    artifact_id: str
    logical_path: str
    sha256: str
    size_bytes: int
    classification: str


def sha256_file(path: str | Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def load_artifact_manifest(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        manifest = json.load(handle)
    if manifest.get("schema_version") != "1.0.0":
        raise ArtifactVerificationError("unsupported artifact-manifest schema")
    if not isinstance(manifest.get("private_artifacts"), dict):
        raise ArtifactVerificationError("manifest lacks private_artifacts")
    return manifest


def identity_from_manifest(manifest: dict[str, Any], artifact_id: str) -> ArtifactIdentity:
    try:
        record = manifest["private_artifacts"][artifact_id]
    except KeyError as exc:
        raise ArtifactVerificationError(f"unknown private artifact: {artifact_id}") from exc
    return ArtifactIdentity(
        artifact_id=artifact_id,
        logical_path=str(record["logical_path"]),
        sha256=str(record["sha256"]),
        size_bytes=int(record["size_bytes"]),
        classification=str(record["classification"]),
    )


def verify_private_artifact(
    path: str | Path,
    identity: ArtifactIdentity,
) -> dict[str, str | int]:
    """Verify size and SHA-256 before any NumPy or JSON parser sees the file."""

    artifact_path = Path(path)
    actual_size = artifact_path.stat().st_size
    if actual_size != identity.size_bytes:
        raise ArtifactHashMismatch(
            f"{identity.artifact_id} size mismatch: expected {identity.size_bytes}, "
            f"got {actual_size}"
        )
    actual_hash = sha256_file(artifact_path)
    if not hmac.compare_digest(actual_hash, identity.sha256):
        raise ArtifactHashMismatch(
            f"{identity.artifact_id} SHA-256 mismatch: expected {identity.sha256}, "
            f"got {actual_hash}"
        )
    return {
        "artifact_id": identity.artifact_id,
        "logical_path": identity.logical_path,
        "sha256": actual_hash,
        "size_bytes": actual_size,
        "status": "verified_before_parse",
    }


def identify_private_artifact(
    path: str | Path,
    manifest: dict[str, Any],
    allowed_artifact_ids: tuple[str, ...],
) -> tuple[ArtifactIdentity, dict[str, str | int]]:
    """Match a file to one of a small, explicitly allowed set of identities."""

    artifact_path = Path(path)
    actual_size = artifact_path.stat().st_size
    actual_hash = sha256_file(artifact_path)
    for artifact_id in allowed_artifact_ids:
        identity = identity_from_manifest(manifest, artifact_id)
        if actual_size == identity.size_bytes and hmac.compare_digest(
            actual_hash, identity.sha256
        ):
            return identity, {
                "artifact_id": identity.artifact_id,
                "logical_path": identity.logical_path,
                "sha256": actual_hash,
                "size_bytes": actual_size,
                "status": "verified_before_parse",
            }
    raise ArtifactHashMismatch(
        f"file does not match any allowed private-artifact identity; "
        f"size={actual_size}, sha256={actual_hash}, allowed={allowed_artifact_ids}"
    )
