#!/bin/bash

source "pyvenv/bin/activate"

# Function to recursively add directories to PYTHONPATH
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

# Add the project root (current dir) to PYTHONPATH
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"

echo "Python path: $PYTHONPATH"

# Recursively add all subdirectories under 'py' to PYTHONPATH
add_to_pythonpath "$PROJECT_ROOT/py"

# Export the modified PYTHONPATH
export PYTHONPATH

# Print the PYTHONPATH for verification
echo "PYTHONPATH: $PYTHONPATH"

# Start the RQ worker
rq worker
