"""Base test class for Alpha testing scenarios with configuration loading."""

import json
import logging
import os
import unittest

from py.render.data_funcs import load_driver_data, load_track_data
from py.utils.config import Config


class SetupAlpha(unittest.TestCase):
    """Base test class for Alpha testing scenarios with configuration loading."""

    def setUp(self):
        """Create the test environment by loading configuration and data.

        Disables logging during tests to reduce noise.
        """
        logging.disable(logging.CRITICAL)

        config_path = os.path.join(os.path.dirname(__file__), "alpha_config.json")
        with open(config_path, "r") as f:
            self.config: Config = json.load(f)

        self.track_data: load_track_data.TrackData = load_track_data.main(
            self.config["year"], self.config["track"]
        )
        self.driver_dfs, self.start_finish_line_idx = load_driver_data.main(
            self.config, self.track_data
        )

    def tearDown(self):
        """Restore normal logging after test completion."""
        logging.disable(logging.NOTSET)
