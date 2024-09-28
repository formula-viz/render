#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
source "$SCRIPT_DIR/scripts/prepare_blender.sh"

# we want to directly invoke render from blender with args such that
# the render doesn't actually happen, we can see the complete blender scene

HEADLESS=false
CONFIG='{
  "track": "SIN",
  "year": 2024,
  "type": "rest-of-field",
  "pipeline": {
    "isolate_module": "render",
    "preview_mode": true,
    "quick_validate_mode": false
  },
  "render": {
    "fps": 30,
    "samples": 32,
    "adaptive_sampling": true,
    "is_4k": true,
    "output": "output.mp4",
    "max_cam_distance": 70,
    "start_buffer_frames": 45,
    "end_buffer_frames": 70
  },
  "drivers": ["TSU", "RIC"]
}'

if [ "$HEADLESS" = true ]; then
    blender -b --python "$PROJECT_ROOT/py/main.py" -- "$CONFIG"
else
    blender --python "$PROJECT_ROOT/py/main.py" -- "$CONFIG"
fi
