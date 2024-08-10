import logging
import os
import sys

MAIN_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
PYTHON_SCRIPTS_ROOT = os.path.join(MAIN_PROJECT_ROOT, "py")
sys.path.append(MAIN_PROJECT_ROOT)
sys.path.append(PYTHON_SCRIPTS_ROOT)
sys.path.append(os.path.dirname(os.path.realpath(__file__)))


import load_ff1
import load_track_data
from utils.read_yaml import read_yaml

logger = logging.getLogger(__name__)


# this need not be run in blender so we don't need to worry about receiving args,
# we can just call as a function in a module like normal
def main(yaml_path: str) -> None:
    try:
        year, track, fps, _, _ = read_yaml(yaml_path)
        load_track_data.main(year, track)
        load_ff1.main(year, track, fps)
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python3 pre_render.py -- <path_to_yaml>")
        sys.exit(1)

    main(sys.argv[3])
