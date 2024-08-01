#!/usr/bin/env python3

import os
import sys
import subprocess
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_root():
    if os.geteuid() != 0:
        logger.error("This script must be run as root (use sudo)")
        sys.exit(1)

def run_command(command):
    try:
        subprocess.run(command, check=True, shell=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed: {e}")
        sys.exit(1)

def activate_venv():
    venv_activate = Path('venv/bin/activate').resolve()
    activate_this = str(venv_activate)
    exec(open(activate_this).read(), {'__file__': activate_this})

def main(yaml_path):
    logger.info("Entering main.py")

    check_root()
    activate_venv()

    run_command("pip install -r ../requirements.txt")

    logger.info("Entering pre_render")
    run_command(f"python3 ../pre_render/pre_render.py {yaml_path}")

    logger.info("Entering render")
    run_command(f"blender --background --python ../render/pre_render.py {yaml_path}")

    logger.info("Entering post_render")
    run_command(f"blender --background --python ../post_render/post_render.py {yaml_path}")

    logger.info("Ending main.py")
