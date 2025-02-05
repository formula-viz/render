import unittest
import os
import json
import logging

from py.render.render_funcs import load_track_data, load_driver_data

class SetupAlpha(unittest.TestCase):
    def setUp(self):
        self.original_level = logging.root.level
        logging.disable(logging.CRITICAL)

        config_path = os.path.join(os.path.dirname(__file__), 'alpha_config.json')
        with open(config_path, 'r') as f:
            self.config = json.load(f)

        self.track_data = load_track_data.main(self.config["year"], self.config["track"])
        self.driver_dfs, self.start_finish_line_idx = load_driver_data.main(self.config, self.track_data)

    def tearDown(self):
        logging.disable(logging.NOTSET)
