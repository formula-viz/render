#!/bin/bash
echo "Entering main.sh"

######################
echo "Entering pre_render"
python pre_render/main.py
######################

#####################
echo "Entering render"
blender --background --python render/main.py
#####################

echo "Ending main.sh"
