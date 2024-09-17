#!/bin/bash

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

VENV_NAME="pyvenv"

# Check if virtual environment exists
if [ ! -d "$VENV_NAME" ]; then
    echo "Creating virtual environment..."
    python3 -m venv $VENV_NAME
else
    echo "Virtual environment already exists."
fi

# Activate virtual environment
source $VENV_NAME/bin/activate

export BLENDER_SYSTEM_PYTHON="$PWD/$VENV_NAME/lib/python3.*/site-packages"

# Install or upgrade pip
pip install --upgrade pip

# Install requirements
if [ -f "requirements.txt" ]; then
    echo "Installing requirements..."
    pip install -r requirements.txt
else
    echo "No requirements.txt found. Skipping package installation."
fi

# Create necessary directories
mkdir -p persistent/data/{track_data,car_data}

# Setup and start Redis
setup_redis

echo $BLENDER_SYSTEM_PYTHON

# Start the application
python3 app.py

# Deactivate virtual environment
deactivate
