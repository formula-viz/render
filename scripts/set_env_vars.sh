#!/bin/bash

export PROJECT_ROOT=$(dirname "$(cd "$(dirname "$0")" && pwd)")
export VENV_PATH="$PROJECT_ROOT/pyvenv"

# blender system python refers to the site packages location
export BLENDER_SYSTEM_PYTHON="$VENV_PATH/lib/python3.*/site-packages"

export REQUIREMENTS_PATH="$PROJECT_ROOT/requirements.txt"

export FLASK_PY_PATH="$PROJECT_ROOT/scripts/start_flask.py"

export FRAMES_DIR="$PROJECT_ROOT/temporary/frames"
rm -rf "$FRAMES_DIR"
mkdir -p "$FRAMES_DIR"

add_to_pythonpath() {
    local dir="$1"
    if [[ "$(basename "$dir")" != "__pycache__" ]]; then
        PYTHONPATH="$dir:$PYTHONPATH"
        for subdir in "$dir"/*/ ; do
            if [ -d "$subdir" ]; then
                add_to_pythonpath "$subdir"
            fi
        done
    fi
}

PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"
# Recursively add all subdirectories under 'py' to PYTHONPATH
add_to_pythonpath "$PROJECT_ROOT/py"
# Export the modified PYTHONPATH
PYTHONPATH="$PROJECT_ROOT/scripts:$PYTHONPATH"

export PYTHONPATH
