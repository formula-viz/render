#!/bin/bash

source venv/bin/activate

YEAR=2024
TRACK="CAN"
SESSION="Q"
DRIVERS=("RUS" "VER")

MAIN_RENDER_OUTPUT="tmp/main_render.fp4"

echo "Before starting blender"

blender --background --python entry.py -- $YEAR $TRACK $SESSION True $MAIN_RENDER_OUTPUT ${DRIVERS[@]} --debug

deactivate
