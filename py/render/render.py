"""Entrypoint for the python blender rendering application. Handles conditional triggering of different ports of the application for development and testing purposes."""

import json
import sys
from typing import cast

from py.render.renderers import HeadToHeadRenderer, RestOfFieldRenderer
from py.utils.config import Config
from py.utils.logger import log_info

if __name__ == "__main__":
    raw_config = json.loads(sys.argv[-1])
    config = cast(Config, raw_config)

    video_type = config["type"]

    renderer = (
        HeadToHeadRenderer(config)
        if video_type == "head-to-head"
        else RestOfFieldRenderer(config)
    )
    log_info(
        f"Starting Render with Config: {config['track']}, {config['year']}, {config['type']}"
    )
    output_path = renderer.render()
