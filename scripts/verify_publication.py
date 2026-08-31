#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-2.1-or-later

from __future__ import annotations

import argparse
import re
import xml.etree.ElementTree as ET
from pathlib import Path


SEMVER = re.compile(
    r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)"
    r"(?:-[0-9A-Za-z]+(?:[.-][0-9A-Za-z]+)*)?"
)
GROUP = "cc.suviomedia"
ARTIFACT = "kmedia-wasm-engine-runtime-assets"


def text(root: ET.Element, path: str, namespace: dict[str, str]) -> str:
    node = root.find(path, namespace)
    if node is None or node.text is None:
        raise ValueError(f"POM field is missing: {path}")
    return node.text.strip()


def verify(staging: Path, version: str) -> None:
    directory = staging / "cc/suviomedia" / ARTIFACT / version
    pom = directory / f"{ARTIFACT}-{version}.pom"
    root = ET.parse(pom).getroot()
    namespace = {"m": "http://maven.apache.org/POM/4.0.0"}
    exact = {
        "m:groupId": GROUP,
        "m:artifactId": ARTIFACT,
        "m:version": version,
        "m:packaging": "zip",
        "m:name": "KMedia Wasm runtime assets",
        "m:description": "Pinned FFmpeg/Emscripten Wasm runtime with complete corresponding source.",
        "m:url": "https://github.com/SuvioMedia/kmedia-wasm-runtime",
        "m:scm/m:connection": "scm:git:https://github.com/SuvioMedia/kmedia-wasm-runtime.git",
        "m:scm/m:developerConnection": "scm:git:ssh://git@github.com/SuvioMedia/kmedia-wasm-runtime.git",
        "m:scm/m:url": "https://github.com/SuvioMedia/kmedia-wasm-runtime",
    }
    for path, expected in exact.items():
        actual = text(root, path, namespace)
        if actual != expected:
            raise ValueError(f"unexpected POM field {path}: {actual!r}")

    developer_ids = {
        (node.text or "").strip()
        for node in root.findall("m:developers/m:developer/m:id", namespace)
    }
    if developer_ids != {"Shusek"}:
        raise ValueError(f"unexpected POM developers: {sorted(developer_ids)}")

    license_names = {
        (node.text or "").strip()
        for node in root.findall("m:licenses/m:license/m:name", namespace)
    }
    expected_licenses = {
        "GNU Lesser General Public License, version 2.1 or later",
        "Bundled component license map and relinking terms",
    }
    if license_names != expected_licenses:
        raise ValueError(f"unexpected POM licenses: {sorted(license_names)}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--staging", type=Path, required=True)
    parser.add_argument("--version", required=True)
    arguments = parser.parse_args()
    if not SEMVER.fullmatch(arguments.version):
        raise ValueError("version must be immutable SemVer")
    verify(arguments.staging.resolve(), arguments.version)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
