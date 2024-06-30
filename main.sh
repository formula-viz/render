#!/bin/bash

YEAR=2024
TRACK="CAN"
SESSION="Q"
DRIVERS=("RUS" "VER")

MAIN_RENDER_OUTPUT="tmp/main_render.fp4"

blender --background --python entry.py -- $YEAR $TRACK $SESSION $MAIN_RENDER_OUTPUT ${DRIVERS[@]}
