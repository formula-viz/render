#!/bin/bash

PROJECT_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Ensure we have the csv repo cloned locally under root dir
if [ -d "csv_repo" ]; then
    # Directory exists, do a pull
    cd csv_repo
    git pull
    cd ..
else
    # Directory doesn't exist, do a clone
    git clone git@github.com:formula-viz/csv_repo.git
fi

/opt/blender/4.0/python/bin/python3.10 -m pip install -r "$PROJECT_ROOT/requirements.txt"
export PYTHONPATH="${PROJECT_ROOT}:${PROJECT_ROOT}/py:${PYTHONPATH:-}"

blender --background --python "$PROJECT_ROOT/tests/run_tests.py"
