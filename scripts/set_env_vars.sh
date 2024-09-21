#!/bin/bash

export PROJECT_ROOT=$(dirname "$(cd "$(dirname "$0")" && pwd)")
export VENV_PATH="$PROJECT_ROOT/pyvenv"

# blender system python refers to the site packages location
export BLENDER_SYSTEM_PYTHON="$VENV_PATH/lib/python3.*/site-packages"

export REQUIREMENTS_PATH="$PROJECT_ROOT/requirements.txt"

export FLASK_PY_PATH="$PROJECT_ROOT/scripts/start_flask.py"


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

# Env Vars which will be used in the Python scripts
python_env_vars() {
    TEMPORARY_DIR="$PROJECT_ROOT/temporary"
    RESOURCES_DIR="$PROJECT_ROOT/resources"
    DATA_DIR="$PROJECT_ROOT/persistent/data"

    export CAR_FBX_PATH="$RESOURCES_DIR/cars/formula-1-2024-generic/source/F1_TexPaintBlender_v01_20210215.fbx"
    export CAR_PAINTS_DIR="$PROJECT_ROOT/temporary/car_paints"
    export CAR_TEXTURES_DIR="$RESOURCES_DIR/cars/formula-1-2024-generic/textures"

    export CAR_DATA_DIR="$DATA_DIR/car_data"
    export DRIVER_TIMES_DIR="$DATA_DIR/driver_times"
    export DRIVER_IMAGES_DIR="$DATA_DIR/driver_images"
    export TRACK_DATA_DIR="$DATA_DIR/track_data"

    export BACKGROUND_MUSIC_PATH="$RESOURCES_DIR/audio/lofi-hiphop-background.m4a"
    export BACKGROUND_IMAGE_PATH="$RESOURCES_DIR/backgrounds/background1.jpeg"
    export MAIN_FONT="$RESOURCES_DIR/fonts/Formula1-Regular.ttf"

    export FRAMES_DIR="$TEMPORARY_DIR/frames"
    rm -rf "$FRAMES_DIR"
    mkdir -p "$FRAMES_DIR"
}


