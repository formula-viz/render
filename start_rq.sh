#!/bin/bash

source "pyvenv/bin/activate"

# Get the absolute path to the project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Add the project root and the 'py' directory to PYTHONPATH
export PYTHONPATH="$PROJECT_ROOT:$PROJECT_ROOT/py:$PYTHONPATH"

# Start the RQ worker
rq worker
