# SPDX-License-Identifier: LGPL-2.1-or-later

import unittest
from pathlib import Path


class ReleaseWorkflowTest(unittest.TestCase):
    def setUp(self) -> None:
        root = Path(__file__).resolve().parents[1]
        self.release = (root / ".github/workflows/release.yml").read_text(encoding="utf-8")
        self.central = (root / ".github/workflows/maven-central.yml").read_text(
            encoding="utf-8"
        )
        self.promote = (root / ".github/workflows/promote-central.yml").read_text(
            encoding="utf-8"
        )

    def test_public_workflows_cannot_use_private_infrastructure(self) -> None:
        for workflow in (self.release, self.central, self.promote):
            self.assertNotIn("self-hosted", workflow)
            self.assertNotIn("repo.suviomedia.cc", workflow)
            self.assertNotIn("kkrepo", workflow.lower())
            self.assertNotIn("suvio-player", workflow)
            self.assertNotIn("suvio-sdk", workflow)
            self.assertIn("runs-on: ubuntu-24.04", workflow)
            self.assertIn("github.triggering_actor == 'Shusek'", workflow)

    def test_release_is_explicit_and_evidence_bound(self) -> None:
        self.assertIn("workflow_dispatch:", self.release)
        self.assertNotIn("tags:", self.release)
        self.assertIn('test "$GITHUB_REF" = refs/heads/main', self.release)
        self.assertIn('test "$(git rev-parse HEAD)" = "$TESTED_COMMIT"', self.release)
        self.assertIn('test "$REBUILD_VERIFIED" = true', self.release)
        self.assertIn("gh release create", self.release)

    def test_central_uses_one_protected_approval_before_automatic_publish(self) -> None:
        self.assertIn("environment: maven-central", self.central)
        self.assertIn("default: AUTOMATIC", self.central)
        self.assertIn("retention-days: 1", self.central)
        self.assertIn("for attempt in {1..240}; do", self.central)
        self.assertNotIn("publishAndReleaseToMavenCentral", self.central)

    def test_manual_staging_can_be_promoted_without_portal_access(self) -> None:
        self.assertIn("environment: maven-central", self.promote)
        self.assertIn("github.triggering_actor == 'Shusek'", self.promote)
        self.assertIn("/api/v1/publisher/deployments", self.promote)
        self.assertIn("/api/v1/publisher/deployment/$deployment", self.promote)
        self.assertIn(
            "pkg:maven/cc.suviomedia/kmedia-wasm-engine-runtime-assets@$VERSION",
            self.promote,
        )
        self.assertIn('.deploymentState == "VALIDATED"', self.promote)
        self.assertIn('test "$(wc -l < "$matches")" -eq 1', self.promote)
        self.assertIn("scripts/verify_publication.py", self.promote)
        self.assertIn("/download/$relative_pom", self.promote)
        self.assertIn('cmp -s "$candidate_pom" "$expected_pom"', self.promote)
        self.assertNotIn(".deploymentName ==", self.promote)

    def test_only_the_public_suviomedia_coordinate_is_bundled(self) -> None:
        root = Path(__file__).resolve().parents[1]
        bundle = (root / "scripts/build_central_bundle.py").read_text(encoding="utf-8")
        self.assertIn('GROUP_PATH = Path("cc/suviomedia")', bundle)
        self.assertIn('ARTIFACT = "kmedia-wasm-engine-runtime-assets"', bundle)
        self.assertNotIn("io/github/shusek", bundle)


if __name__ == "__main__":
    unittest.main()
