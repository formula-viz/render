#!/bin/bash

PROJECT_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

/opt/blender/4.0/python/bin/python3.10 -m pip install -r "$PROJECT_ROOT/requirements.txt"
export PYTHONPATH="${PROJECT_ROOT}:${PROJECT_ROOT}/py:${PYTHONPATH:-}"

blender --background --python "$PROJECT_ROOT/tests/run_tests.py"
