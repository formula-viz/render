#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
source "$SCRIPT_DIR/prepare_blender.sh"

# we want to directly invoke render from blender with args such that
# the render doesn't actually happen, we can see the complete blender scene

CONFIG='{
  "track": "SIN",
  "year": 2024,
  "type": "head-to-head",
  "render": {
    "should_render": false,
    "validate_render": true,
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

blender --python "$PROJECT_ROOT/py/post_render/post_render.py" -- "$CONFIG"
