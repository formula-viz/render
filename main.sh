#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
source "$SCRIPT_DIR/scripts/prepare_blender.sh"

CONFIG_FILE="$PROJECT_ROOT/config.json"
TEMPLATE_FILE="$PROJECT_ROOT/config.json.template"

if [ ! -f "$CONFIG_FILE" ]; then
    if [ ! -f "$TEMPLATE_FILE" ]; then
        echo "Error: config.json.template not found. Cannot create config.json."
        exit 1
    fi

    cp "$TEMPLATE_FILE" "$CONFIG_FILE"
    echo "config.json has been created. Please edit it with your specific configuration values and run the script again."
    exit 0
fi

CONFIG=$(cat "$PROJECT_ROOT/config.json")

PREVIEW_MODE=$(echo "$CONFIG" | jq -r '.pipeline.preview_mode')
if [ "$PREVIEW_MODE" = true ]; then
    blender -b --python "$PROJECT_ROOT/py/main.py" -- "$CONFIG"
else
    blender --python "$PROJECT_ROOT/py/main.py" -- "$CONFIG"
fi
