#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
source "$SCRIPT_DIR/scripts/prepare_blender.sh"

blender --background --python "$PROJECT_ROOT/tests/run_tests.py"
