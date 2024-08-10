#!/usr/bin/env python3

import logging
import os
import subprocess
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(filename)s:%(lineno)d - %(funcName)s - [%(threadName)s] - %(message)s",
)
logger = logging.getLogger(__name__)

MAIN_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
PYTHON_SCRIPTS_ROOT = os.path.join(MAIN_PROJECT_ROOT, "py")
sys.path.append(MAIN_PROJECT_ROOT)
sys.path.append(PYTHON_SCRIPTS_ROOT)
sys.path.append(os.path.dirname(os.path.realpath(__file__)))

from utils.project_structure import (get_bash_venv_path, get_post_render_path,
                                     get_pre_render_path, get_render_path,
                                     get_requirements_path)


def check_root():
    if os.geteuid() != 0:
        logger.error("This script must be run as root (use sudo)")
        sys.exit(1)


def main(yaml_path):
    logger.info("Entering main.py")

    check_root()

    commands_to_run = [
        f"source {get_bash_venv_path()}",
        f"pip install -r {get_requirements_path()}",
        f"python {get_pre_render_path()} {yaml_path}",
        f"blender --background --python {get_render_path()} {yaml_path}",
        f"blender --background --python {get_post_render_path()} {yaml_path}",
    ]

    subprocess.run(" && ".join(commands_to_run), shell=True, executable="/bin/bash")

    logger.info("Ending main.py")
