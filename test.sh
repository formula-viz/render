#!/bin/bash

PROJECT_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

/opt/blender/4.0/python/bin/python3.10 -m pip install -r "$PROJECT_ROOT/requirements.txt"
export PYTHONPATH="${PROJECT_ROOT}:${PROJECT_ROOT}/py:${PYTHONPATH:-}"

# Check if run-external-api-tests flag is present
if [[ "$*" == *--run-external-api-tests* ]]; then
  blender -b --python "$PROJECT_ROOT/tests/run_tests.py" -- --run-external-api-tests
else
  blender -b --python "$PROJECT_ROOT/tests/run_tests.py"
fi
