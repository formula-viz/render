#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
source "$SCRIPT_DIR/set_env_vars.sh"

source "$VENV_PATH/bin/activate"

echo "PYTHONPATH: $PYTHONPATH"

rq worker
