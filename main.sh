#!/bin/bash

# ensure directories are created
mkdir -p persistent/data/track_data
mkdir -p persistent/data/car_data

source py/venv/bin/activate

pip install -r py/requirements.txt

python3 py/render_queue/render_queue.py
