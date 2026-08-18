import unittest

from scripts.resolve_release import decide_release, release_revisions


class ReleaseResolutionTests(unittest.TestCase):
    def test_first_release_uses_revision_one(self) -> None:
        decision = decide_release([], "2.0.0", image_inputs_changed=False)

        self.assertEqual(decision.revision, 1)
        self.assertTrue(decision.should_publish)

    def test_unchanged_image_inputs_skip_existing_release(self) -> None:
        decision = decide_release(
            ["v2.0.0-r1", "v2.0.0-r3"], "2.0.0", image_inputs_changed=False
        )

        self.assertEqual(decision.revision, 3)
        self.assertFalse(decision.should_publish)

    def test_changed_image_inputs_increment_release_revision(self) -> None:
        decision = decide_release(["v2.0.0-r1"], "2.0.0", image_inputs_changed=True)

        self.assertEqual(decision.revision, 2)
        self.assertTrue(decision.should_publish)
        self.assertEqual(decision.tag_for("2.0.0"), "v2.0.0-r2")

    def test_release_revisions_ignore_invalid_tags(self) -> None:
        revisions = release_revisions(
            ["v2.0.0-r1", "v2.0.0-r01", "v2.0.0-r0", "v2.0.1-r4"], "2.0.0"
        )

        self.assertEqual(revisions, [1])
