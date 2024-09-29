#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
source "$SCRIPT_DIR/scripts/prepare_blender.sh"

CONFIG=$(cat "$PROJECT_ROOT/config.json")

PREVIEW_MODE=$(echo "$CONFIG" | jq -r '.pipeline.preview_mode')
if [ "$PREVIEW_MODE" = true ]; then
    blender -b --python "$PROJECT_ROOT/py/main.py" -- "$CONFIG"
else
    blender --python "$PROJECT_ROOT/py/main.py" -- "$CONFIG"
fi
