#!/bin/bash
echo "Entering main.sh"

if [ "$EUID" -ne 0 ]; then
  echo "This script must be run as root (use sudo)" >&2
  exit 1
fi

######################
# Get the directory of the current script
SCRIPT_DIR="$(dirname "$(realpath "$0")")"
# Set the project root to the parent directory of the script directory
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
export PROJECT_ROOT
echo "Project Root: $PROJECT_ROOT"

BLENDER_SYSTEM_PATH="venv/lib/python3.11"
export BLENDER_SYSTEM_PATH
######################

######################
echo "Entering pre_render"
source venv/bin/activate
pip install -r requirements.txt
python3 pre_render/main.py "yaml"
######################

#####################
echo "Entering render"
blender --background --python render/main.py
#####################

#####################
echo "Entering post_render"
blender --background --python post_render/main.py
#####################

echo "Ending main.sh"
deactivate

