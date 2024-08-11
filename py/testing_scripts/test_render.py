import logging
import os
import subprocess
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def main():
    current_dir = os.path.dirname(os.path.abspath(__file__))

    yaml_path = os.path.join(current_dir, "test.yaml")
    if not os.path.exists(yaml_path):
        logger.error(f"File {yaml_path} not found")
        sys.exit(1)

    # activate the virtual env, we assume we're using fish
    # run_command("source ../venv/bin/activate.fish")
    # now ensure we have installed requirements.txt
    subprocess.run("pip install -r ../requirements.txt", shell=True, executable="/bin/bash")

    # now run render through blender, ensuring it is not in headless mode
    subprocess.run(f"blender --python ../render/render.py -- {yaml_path}", shell=True, executable="/bin/bash")


main()
