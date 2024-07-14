#!/bin/bash
echo "Entering main.sh"

######################
echo "Entering pre_render"
source venv/bin/activate
pip install -r pre_render/requirements.txt
python3 pre_render/main.py
######################

#####################
echo "Entering render"
blender --background --python render/main.py
#####################

#####################
echo "Entering post_render"
blender --background --python post_render/main.py
#####################

echo "Ending main.sh"
deactivate

