import unittest
from pathlib import Path


class ReleaseWorkflowTests(unittest.TestCase):
    def test_marker_version_flows_through_prepare_output(self) -> None:
        workflow = Path(".github/workflows/release.yml").read_text(encoding="utf-8")

        self.assertIn(
            "marker_version: ${{ steps.version.outputs.marker_version }}", workflow
        )
        self.assertIn('echo "marker_version=$MARKER_VERSION" >> "$GITHUB_OUTPUT"', workflow)
        downstream_jobs = workflow[workflow.index("  verify:") : workflow.index("  publish:")]
        self.assertNotIn(
            "MARKER_VERSION: ${{ needs.resolve.outputs.marker_version }}", downstream_jobs
        )
        self.assertEqual(
            downstream_jobs.count(
                "MARKER_VERSION: ${{ needs.prepare.outputs.marker_version }}"
            ),
            2,
        )
