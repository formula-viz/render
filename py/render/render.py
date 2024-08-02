import os
import sys

import bpy

MAIN_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
PYTHON_SCRIPTS_ROOT = os.path.join(MAIN_PROJECT_ROOT, "py")
sys.path.append(MAIN_PROJECT_ROOT)
sys.path.append(PYTHON_SCRIPTS_ROOT)
sys.path.append(os.path.dirname(os.path.realpath(__file__)))


import add_camera
import add_driver_objects
import add_sun
import add_track
import render_animation
from utils.project_structure import get_car_textures_dir
from utils.read_yaml import read_yaml


# we already have loaded the track data and the car data for all cars
# on this year and track, now, we just need the cars to render
def main(yaml_path):
    print(f"YAML_PATH: {yaml_path}")
    year, track, fps, drivers, config = read_yaml(yaml_path)

    print(config)

    bpy.data.collections.remove(bpy.data.collections["Collection"], do_unlink=True)
    bpy.context.scene.world.node_tree.nodes["Background"].inputs[0].default_value = (0.6, 0.6, 0.6, 1)
    add_sun.main()

    print("Adding Track...")
    add_track.main(str(year), track)

    print("Adding Drivers...")
    focused_driver = drivers[0][0]  # the camera driver is just the first listed
    driver_objs, driver_dfs = add_driver_objects.main(str(year), track, str(fps), drivers)

    add_camera.main(driver_dfs[focused_driver], driver_objs[focused_driver])
    bpy.ops.file.find_missing_files(directory=get_car_textures_dir())

    render_settings = config["render"]
    if render_settings["should_render"]:
        print("Starting Rendering...")
        render_animation.main(render_settings, len(driver_dfs[focused_driver]))
    else:
        print("should_render is set to false, skipping rendering...")

    print("End script")


if __name__ == "__main__":
    if len(sys.argv) < 5:
        print("Usage: blender --python render.py -- <path_to_yaml>")
        sys.exit(1)

    main(sys.argv[4])
