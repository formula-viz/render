#!/bin/bash
echo "Entering main.sh"

######################
# Get the directory of the current script
SCRIPT_DIR="$(dirname "$(realpath "$0")")"
# Set the project root to the parent directory of the script directory
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
export PROJECT_ROOT
echo "Project Root: $PROJECT_ROOT"
######################

######################
echo "Entering pre_render"
source venv/bin/activate
pip install -r requirements.txt
python3 pre_render/main.py "yaml"
######################

#####################
echo "Entering render"
# blender --background --python render/main.py
blender --python render/main.py
#####################

#####################
echo "Entering post_render"
blender --background --python post_render/main.py
#####################

echo "Ending main.sh"
deactivate

