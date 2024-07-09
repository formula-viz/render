#!/bin/bash

# by default this seems to be git ignored, ensuring cache dirs exist here
mkdir cache
mkdir cache/track_data

source venv/bin/activate

export OPTIX_PATH=~/Install/optix-build/bin

YEAR=2024
TRACK="CAN"
SESSION="Q"
DRIVERS=("RUS" "VER")

MAIN_RENDER_OUTPUT="tmp/main_render.fp4"

echo "Before starting blender"

blender --background --python entry.py -- $YEAR $TRACK $SESSION True $MAIN_RENDER_OUTPUT ${DRIVERS[@]}

deactivate
