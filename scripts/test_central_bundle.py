# SPDX-License-Identifier: LGPL-2.1-or-later

from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("build_central_bundle.py")
SPEC = importlib.util.spec_from_file_location("central_bundle", MODULE_PATH)
central = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(central)


class CentralBundleTest(unittest.TestCase):
    def stage_primary(self, staging: Path, version: str) -> set[Path]:
        expected = central.expected_primary(version)
        for relative in expected:
            path = staging / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"artifact")
        return expected

    def test_normalize_removes_only_gradle_generated_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as value:
            staging = Path(value)
            version = "1.0.0-rc.1"
            expected = self.stage_primary(staging, version)
            for relative in expected:
                for suffix in central.GENERATED_CHECKSUM_SUFFIXES:
                    (staging / relative.with_name(relative.name + suffix)).write_bytes(b"generated")
            metadata = staging / central.GROUP_PATH / central.ARTIFACT / "maven-metadata.xml"
            metadata.write_bytes(b"generated")
            for suffix in central.GENERATED_CHECKSUM_SUFFIXES:
                metadata.with_name(metadata.name + suffix).write_bytes(b"generated")

            central.normalize_staging(staging, version)

            actual = {path.relative_to(staging) for path in staging.rglob("*") if path.is_file()}
            self.assertEqual(expected, actual)

    def test_normalize_rejects_an_extra_publication(self) -> None:
        with tempfile.TemporaryDirectory() as value:
            staging = Path(value)
            version = "1.0.0-rc.1"
            self.stage_primary(staging, version)
            extra = staging / central.GROUP_PATH / "private-player" / version / "private.pom"
            extra.parent.mkdir(parents=True)
            extra.write_bytes(b"private")
            with self.assertRaisesRegex(ValueError, "closed inventory"):
                central.normalize_staging(staging, version)

    def test_bundle_contains_only_signed_closed_inventory(self) -> None:
        with tempfile.TemporaryDirectory() as value:
            root = Path(value)
            staging = root / "staging"
            version = "1.0.0-rc.1"
            primary = self.stage_primary(staging, version)
            expected: set[str] = set()
            for relative in primary:
                signature = staging / relative.with_name(relative.name + ".asc")
                signature.write_bytes(b"signature")
                name = relative.as_posix()
                expected.update(
                    {
                        name,
                        name + ".asc",
                        name + ".md5",
                        name + ".sha1",
                        name + ".asc.md5",
                        name + ".asc.sha1",
                    }
                )
            bundle = root / "central.zip"

            subprocess.run(
                [
                    sys.executable,
                    str(MODULE_PATH),
                    "--staging",
                    str(staging),
                    "--version",
                    version,
                    "--epoch",
                    "1700000000",
                    "--output",
                    str(bundle),
                ],
                check=True,
            )

            with zipfile.ZipFile(bundle) as archive:
                self.assertEqual(expected, set(archive.namelist()))


if __name__ == "__main__":
    unittest.main()
