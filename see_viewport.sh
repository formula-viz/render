#!/bin/bash
# for testing, stops before starting rendering, opens blender in normal mode

YEAR=2024
TRACK="CAN"
SESSION="Q"
DRIVERS=("RUS" "VER")

MAIN_RENDER_OUTPUT="tmp/main_render.fp4"

blender --debug --python entry.py -- $YEAR $TRACK $SESSION False $MAIN_RENDER_OUTPUT ${DRIVERS[@]}
