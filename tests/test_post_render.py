import logging
import os
import subprocess
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def run_command(command):
    try:
        subprocess.run(command, check=True, shell=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed: {e}")
        sys.exit(1)


def main():
    current_dir = os.path.dirname(os.path.abspath(__file__))

    yaml_path = os.path.join(current_dir, "test.yaml")
    if not os.path.exists(yaml_path):
        logger.error(f"File {yaml_path} not found")
        sys.exit(1)

    test_frames = os.path.join(current_dir, "test_frames")
    if not os.path.exists(test_frames):
        logger.error(f"Directory {test_frames} not found")
        sys.exit(1)

    # now run render through blender, ensuring it is not in headless mode
    run_command(f"blender --python ../post_render/post_render.py -- {yaml_path} {test_frames}")


main()
