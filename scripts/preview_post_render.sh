#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
source "$SCRIPT_DIR/prepare_blender.sh"

# we want to directly invoke render from blender with args such that
# the render doesn't actually happen, we can see the complete blender scene

# the config for this test is within render.py
blender --python "$PROJECT_ROOT/py/post_render/post_render.py" -- "testing"
