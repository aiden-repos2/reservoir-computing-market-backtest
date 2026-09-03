"""Deterministic allowlist manifest for the public source release.

The manifest inventories the files intended for publication.  Runtime debris
created by an editable install or a test run is deliberately outside that
allowlist; sensitive arrays, compiled objects, archives, and symlinks are
rejected even if somebody attempts to add them to the manifest.
"""

from __future__ import annotations

import csv
import hashlib
import subprocess
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Iterable


MANIFEST_RELATIVE_PATH = PurePosixPath("evidence/RELEASE_MANIFEST.csv")
MANIFEST_COLUMNS = ("path", "bytes", "sha256")

# These locations are working-environment state, not source-release content.
IGNORED_DIRECTORY_NAMES = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "htmlcov",
    "build",
    "dist",
    "__MACOSX",
}
IGNORED_DIRECTORY_SUFFIXES = (".egg-info",)
IGNORED_FILE_NAMES = {".DS_Store", ".coverage"}

# These formats must never be part of this source-only public release.
FORBIDDEN_SUFFIXES = {
    ".npz",
    ".npy",
    ".parquet",
    ".pkl",
    ".pickle",
    ".pyc",
    ".pyo",
    ".so",
    ".dylib",
    ".dll",
    ".o",
    ".a",
    ".exe",
    ".zip",
    ".tar",
    ".tgz",
    ".gz",
    ".bz2",
    ".xz",
    ".7z",
    ".rar",
}
FORBIDDEN_PATH_PREFIXES = (
    PurePosixPath("data/raw"),
    PurePosixPath("data/features"),
    PurePosixPath("data/derived"),
    PurePosixPath("evidence/private"),
    PurePosixPath("results/private"),
    PurePosixPath("private_source_derived"),
)


class ReleaseManifestError(ValueError):
    """Raised when the release allowlist or source tree fails validation."""


@dataclass(frozen=True)
class ReleaseFile:
    path: str
    size_bytes: int
    sha256: str


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _is_ignored_directory_name(name: str) -> bool:
    return name in IGNORED_DIRECTORY_NAMES or name.endswith(
        IGNORED_DIRECTORY_SUFFIXES
    )


def _validate_relative_path(value: str) -> PurePosixPath:
    if not value or "\\" in value:
        raise ReleaseManifestError(f"invalid manifest path: {value!r}")
    path = PurePosixPath(value)
    if path.is_absolute() or value != path.as_posix() or ".." in path.parts:
        raise ReleaseManifestError(f"unsafe manifest path: {value!r}")
    if path == MANIFEST_RELATIVE_PATH:
        raise ReleaseManifestError("release manifest must not inventory itself")
    return path


def _path_is_forbidden(path: PurePosixPath) -> bool:
    if path.name in IGNORED_FILE_NAMES:
        return True
    if any(_is_ignored_directory_name(part) for part in path.parts[:-1]):
        return True
    if path.suffix.lower() in FORBIDDEN_SUFFIXES:
        return True
    return any(path == prefix or prefix in path.parents for prefix in FORBIDDEN_PATH_PREFIXES)


def _walk_release_candidates(root: Path) -> tuple[list[Path], list[str]]:
    """Return publishable file candidates and unconditional tree violations."""

    files: list[Path] = []
    violations: list[str] = []
    stack = [root]
    while stack:
        directory = stack.pop()
        for path in sorted(directory.iterdir(), key=lambda item: item.name):
            relative = PurePosixPath(path.relative_to(root).as_posix())
            if path.is_symlink():
                # Ignore symlinks inside excluded virtual environments only;
                # those directories never enter this traversal.
                violations.append(f"symlink:{relative.as_posix()}")
                continue
            if path.is_dir():
                if _is_ignored_directory_name(path.name):
                    continue
                stack.append(path)
                continue
            if not path.is_file():
                violations.append(f"nonregular:{relative.as_posix()}")
                continue
            if relative == MANIFEST_RELATIVE_PATH:
                continue
            if _path_is_forbidden(relative):
                violations.append(f"forbidden:{relative.as_posix()}")
                continue
            files.append(path)
    return sorted(files, key=lambda item: item.relative_to(root).as_posix()), violations


def build_release_records(root: str | Path) -> list[ReleaseFile]:
    """Build deterministic records for all intended public files in ``root``."""

    repository = Path(root).resolve()
    files, violations = _walk_release_candidates(repository)
    if violations:
        raise ReleaseManifestError(
            f"release-tree violations found: {sorted(set(violations))}"
        )
    return [
        ReleaseFile(
            path=path.relative_to(repository).as_posix(),
            size_bytes=path.stat().st_size,
            sha256=_sha256(path),
        )
        for path in files
    ]


def write_release_manifest(root: str | Path) -> Path:
    """Regenerate the CSV manifest after reviewing the complete release tree."""

    repository = Path(root).resolve()
    records = build_release_records(repository)
    destination = repository / Path(MANIFEST_RELATIVE_PATH.as_posix())
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(MANIFEST_COLUMNS)
        for record in records:
            writer.writerow((record.path, record.size_bytes, record.sha256))
    return destination


def load_release_manifest(path: str | Path) -> list[ReleaseFile]:
    manifest_path = Path(path)
    with manifest_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != MANIFEST_COLUMNS:
            raise ReleaseManifestError(
                f"manifest header must be exactly {MANIFEST_COLUMNS}"
            )
        rows = list(reader)
    if not rows:
        raise ReleaseManifestError("release manifest is empty")

    records: list[ReleaseFile] = []
    for row in rows:
        relative = _validate_relative_path(row["path"])
        if _path_is_forbidden(relative):
            raise ReleaseManifestError(
                f"forbidden file appears in release manifest: {relative.as_posix()}"
            )
        try:
            size_bytes = int(row["bytes"])
        except (TypeError, ValueError) as error:
            raise ReleaseManifestError(
                f"invalid byte count for {relative.as_posix()}"
            ) from error
        sha256 = row["sha256"].lower()
        if size_bytes < 0 or len(sha256) != 64 or any(
            character not in "0123456789abcdef" for character in sha256
        ):
            raise ReleaseManifestError(
                f"invalid identity for {relative.as_posix()}"
            )
        records.append(ReleaseFile(relative.as_posix(), size_bytes, sha256))

    paths = [record.path for record in records]
    if paths != sorted(paths) or len(paths) != len(set(paths)):
        raise ReleaseManifestError("manifest paths must be unique and sorted")
    return records


def verify_release_manifest(root: str | Path) -> dict[str, int | str]:
    """Verify that the public allowlist exactly matches the source tree."""

    repository = Path(root).resolve()
    manifest_path = repository / Path(MANIFEST_RELATIVE_PATH.as_posix())
    expected = load_release_manifest(manifest_path)
    actual = build_release_records(repository)
    expected_by_path = {record.path: record for record in expected}
    actual_by_path = {record.path: record for record in actual}
    missing = sorted(set(expected_by_path) - set(actual_by_path))
    unexpected = sorted(set(actual_by_path) - set(expected_by_path))
    changed = sorted(
        path
        for path in set(expected_by_path) & set(actual_by_path)
        if expected_by_path[path] != actual_by_path[path]
    )
    if missing or unexpected or changed:
        raise ReleaseManifestError(
            "release manifest mismatch: "
            f"missing={missing}, unexpected={unexpected}, changed={changed}"
        )
    result: dict[str, int | str] = {
        "status": "exact_allowlist_match",
        "file_count": len(expected),
        "total_bytes": sum(record.size_bytes for record in expected),
    }
    git_marker = repository / ".git"
    if git_marker.exists():
        try:
            completed = subprocess.run(
                ["git", "-C", str(repository), "ls-files", "-z"],
                check=True,
                capture_output=True,
            )
            tracked = {
                item.decode("utf-8")
                for item in completed.stdout.split(b"\0")
                if item
            }
        except (OSError, UnicodeDecodeError, subprocess.CalledProcessError) as error:
            raise ReleaseManifestError("could not inspect the Git index") from error
        tracked.discard(MANIFEST_RELATIVE_PATH.as_posix())
        expected_paths = set(expected_by_path)
        if tracked != expected_paths:
            raise ReleaseManifestError(
                "git index differs from release manifest: "
                f"unmanifested_tracked={sorted(tracked - expected_paths)}, "
                f"manifested_untracked={sorted(expected_paths - tracked)}"
            )
        result["git_index"] = "exact_allowlist_match"
        result["tracked_file_count_excluding_manifest"] = len(tracked)
    else:
        result["git_index"] = "not_available_before_repository_initialization"
    return result


def validate_manifest_paths(records: Iterable[ReleaseFile]) -> list[str]:
    """Return paths after enforcing the public-boundary rules."""

    result: list[str] = []
    for record in records:
        relative = _validate_relative_path(record.path)
        if _path_is_forbidden(relative):
            raise ReleaseManifestError(
                f"forbidden file appears in release manifest: {relative.as_posix()}"
            )
        result.append(relative.as_posix())
    return result
