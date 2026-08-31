#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-2.1-or-later

from __future__ import annotations

import argparse
import hashlib
import re
import time
import zipfile
from pathlib import Path


SEMVER = re.compile(
    r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)"
    r"(?:-[0-9A-Za-z]+(?:[.-][0-9A-Za-z]+)*)?"
)
GROUP_PATH = Path("cc/suviomedia")
ARTIFACT = "kmedia-wasm-engine-runtime-assets"
GENERATED_CHECKSUM_SUFFIXES = (".md5", ".sha1", ".sha256", ".sha512")


def expected_primary(version: str) -> set[Path]:
    prefix = f"{ARTIFACT}-{version}"
    directory = GROUP_PATH / ARTIFACT / version
    return {
        directory / f"{prefix}.zip",
        directory / f"{prefix}-sources.jar",
        directory / f"{prefix}-javadoc.jar",
        directory / f"{prefix}.pom",
    }


def digest(path: Path, algorithm: str) -> str:
    value = hashlib.new(algorithm)
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def real_files(staging: Path) -> set[Path]:
    files: set[Path] = set()
    for path in staging.rglob("*"):
        if path.is_symlink():
            raise ValueError("staging contains a symbolic link")
        if path.is_file():
            files.add(path)
    return files


def normalize_staging(staging: Path, version: str) -> None:
    """Remove only Gradle repository metadata and generated checksum sidecars."""
    for path in sorted(real_files(staging)):
        relative = path.relative_to(staging)
        is_metadata = (
            relative == GROUP_PATH / ARTIFACT / "maven-metadata.xml"
            or any(
                relative == GROUP_PATH / ARTIFACT / ("maven-metadata.xml" + suffix)
                for suffix in GENERATED_CHECKSUM_SUFFIXES
            )
        )
        is_version_checksum = (
            relative.parent == GROUP_PATH / ARTIFACT / version
            and relative.name.endswith(GENERATED_CHECKSUM_SUFFIXES)
        )
        if is_metadata or is_version_checksum:
            path.unlink()

    actual = {path.relative_to(staging) for path in real_files(staging)}
    expected = expected_primary(version)
    if actual != expected:
        raise ValueError(
            "staged Maven publication differs from the closed inventory: "
            f"missing={sorted(map(str, expected - actual))}, "
            f"extra={sorted(map(str, actual - expected))}"
        )


def build_bundle(staging: Path, version: str, epoch: int, output: Path) -> None:
    expected = expected_primary(version)
    primary = {
        path.relative_to(staging)
        for path in real_files(staging)
        if not path.name.endswith((".asc", ".md5", ".sha1"))
    }
    if primary != expected:
        raise ValueError("signed staging differs from the closed primary inventory")

    signed = set(expected)
    for relative in sorted(expected):
        signature = relative.with_name(relative.name + ".asc")
        signature_path = staging / signature
        if not signature_path.is_file() or signature_path.stat().st_size == 0:
            raise ValueError(f"signature is missing: {relative}")
        signed.add(signature)

    actual_before_checksums = {path.relative_to(staging) for path in real_files(staging)}
    if actual_before_checksums != signed:
        raise ValueError("staging contains an unexpected file before checksum generation")

    allowed = set(signed)
    for relative in sorted(signed):
        path = staging / relative
        for algorithm in ("md5", "sha1"):
            sidecar = relative.with_name(relative.name + "." + algorithm)
            (staging / sidecar).write_text(digest(path, algorithm), encoding="ascii")
            allowed.add(sidecar)

    actual = {path.relative_to(staging) for path in real_files(staging)}
    if actual != allowed:
        raise ValueError("staging contains unexpected unsigned or checksum files")
    if output.exists():
        raise ValueError("output already exists")

    timestamp = tuple(time.gmtime(max(epoch, 315532800))[:6])
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for relative in sorted(actual):
            info = zipfile.ZipInfo(relative.as_posix(), timestamp)
            info.external_attr = 0o100644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, (staging / relative).read_bytes())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--staging", type=Path, required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--epoch", type=int)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--normalize", action="store_true")
    arguments = parser.parse_args()
    if not SEMVER.fullmatch(arguments.version):
        raise ValueError("version must be immutable SemVer")

    staging = arguments.staging.resolve()
    if not staging.is_dir() or staging.is_symlink():
        raise ValueError("staging must be a real directory")
    if arguments.normalize:
        if arguments.epoch is not None or arguments.output is not None:
            raise ValueError("normalization does not accept bundle output arguments")
        normalize_staging(staging, arguments.version)
        return 0
    if arguments.epoch is None or arguments.output is None:
        raise ValueError("bundle creation requires --epoch and --output")
    build_bundle(staging, arguments.version, arguments.epoch, arguments.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
