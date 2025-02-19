#!/bin/bash
set -e

PROJECT_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

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

# Ensure we have the csv repo cloned locally under root dir
if [ -d "csv_repo" ]; then
    # Directory exists, do a pull
    cd csv_repo
    git pull
    cd ..
else
    # Directory doesn't exist, do a clone
    git clone git@github.com:formula-viz/csv_repo.git
    echo "csv_repo has been cloned at: $(pwd)/csv_repo"
fi

/opt/blender/4.0/python/bin/python3.10 -m pip install -r "$PROJECT_ROOT/requirements.txt"
export PYTHONPATH="${PROJECT_ROOT}:${PROJECT_ROOT}/py:${PYTHONPATH:-}"

CONFIG=$(cat "$PROJECT_ROOT/config.json")

PREVIEW_MODE=$(echo "$CONFIG" | jq -r '.pipeline.preview_mode')
if [ "$PREVIEW_MODE" = true ]; then
    blender --python "$PROJECT_ROOT/py/main.py" -- "$CONFIG"
    BLENDER_EXIT_CODE=$?
else
    blender --python "$PROJECT_ROOT/py/main.py" -- "$CONFIG"
    BLENDER_EXIT_CODE=$?
fi

if [ "$BLENDER_EXIT_CODE" -ne 0 ]; then
    echo "Blender exited with error code $BLENDER_EXIT_CODE"
    exit 1
fi
