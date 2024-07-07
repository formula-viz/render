#!/bin/bash
# for testing, stops before starting rendering, opens blender in normal mode

# by default this seems to be git ignored, ensuring cache dirs exist here
mkdir cache
mkdir cache/track_data

source venv/bin/activate

YEAR=2024
TRACK="CAN"
SESSION="Q"
DRIVERS=("RUS" "VER")

MAIN_RENDER_OUTPUT="tmp/main_render.fp4"

blender --debug --python entry.py -- $YEAR $TRACK $SESSION False $MAIN_RENDER_OUTPUT ${DRIVERS[@]}
