#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
source "$SCRIPT_DIR/set_env_vars.sh"

set -e  # Exit immediately if a command exits with a non-zero status

# Function to execute command with sudo if necessary
sudo_cmd() {
    if [ "$(id -u)" -ne 0 ]; then
        sudo "$@"
    else
        "$@"
    fi
}

# Function to check and install Redis
setup_redis() {
    echo "Checking Redis installation..."
    if ! command -v redis-server &> /dev/null; then
        echo "Redis not found. Attempting to install Redis..."
        sudo_cmd apt-get update || true
        sudo_cmd apt-get install -y redis-server || {
            echo "Failed to install Redis. Please install it manually and try again."
            exit 1
        }
    else
        echo "Redis is already installed."
    fi

    echo "Checking Redis service status..."
    if ! systemctl is-active --quiet redis-server; then
        echo "Redis service is not active. Attempting to start..."
        sudo_cmd systemctl start redis-server || {
            echo "Failed to start Redis service. Diagnostic information:"
            echo "1. Service status:"
            sudo_cmd systemctl status redis-server
            echo "2. Redis server installation:"
            dpkg -l | grep redis-server
            echo "3. Redis configuration:"
            sudo_cmd cat /etc/redis/redis.conf | grep -v "^#" | grep -v "^$"
            echo "Please review the above information and ensure Redis is correctly installed and configured."
            exit 1
        }
    else
        echo "Redis service is active and running."
    fi
}

# Check if virtual environment exists
if [ ! -d "$VENV_PATH" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_PATH"
else
    echo "Virtual environment already exists."
fi

# Activate virtual environment
source "$VENV_PATH/bin/activate"

# Install or upgrade pip
pip install --upgrade pip

# Install requirements
if [ -f "$REQUIREMENTS_PATH" ]; then
    echo "Installing requirements..."
    pip install -r "$REQUIREMENTS_PATH"
else
    echo "Requirements file not found: $REQUIREMENTS_PATH"
    exit 1
fi

mkdir -p "$PROJECT_ROOT/persistent/data/{track_data,car_data}"

setup_redis

python3 "$FLASK_PY_PATH"

deactivate
