"""Tests for YouTube upload functionality."""

from py.socials import upload_to_yt
from tests.bases import SetupAlpha
from tests.run_tests import skip_external_api


class TestUploadToYT(SetupAlpha):
    """Tests for YouTube upload functionality."""

    @skip_external_api
    def test_upload(self):
        """Tests the YouTube video upload functionality."""
        # Create a copy of the config to avoid modifying the original
        try:
            test_config = self.config.copy()
            test_config["socials"]["youtube"]["visibility"] = "unlisted"
            response = upload_to_yt.main(test_config, "tests/sample-output.mp4")

            self.assertIsNotNone(response, "Upload response should not be None")
            self.assertTrue(
                isinstance(response, dict), "Upload response should be a dictionary"
            )
            self.assertIn("id", response, "Upload response should contain video ID")
        except Exception as e:
            self.fail(f"YouTube upload test failed: {e}")
