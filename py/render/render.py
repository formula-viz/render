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
import add_indicators
import add_sun
import add_track
import load_track_data
import render_animation
from utils.read_yaml import read_yaml


# we already have loaded the track data and the car data for all cars
# on this year and track, now, we just need the cars to render
def main(yaml_path):
    print(f"YAML_PATH: {yaml_path}")
    year, track, fps, drivers, config = read_yaml(yaml_path)

    print(config)

    bpy.data.collections.remove(bpy.data.collections["Collection"], do_unlink=True)
    add_sun.main()

    print("Loading Track Data...")
    inner_points, outer_points, inner_curb_points, outer_curb_points = load_track_data.main(year, track)

    print("Adding Track...")
    add_track.main(inner_points, outer_points, inner_curb_points, outer_curb_points)

    print("Adding Drivers...")
    focused_driver = drivers[0][0]  # the camera driver is just the first listed
    driver_objs, driver_dfs = add_driver_objects.main(str(year), track, str(fps), drivers)

    print("Adding Indicators...")
    add_indicators.main(inner_points, outer_points, inner_curb_points, outer_curb_points, driver_dfs[focused_driver], 0)

    render_settings = config["render"]

    add_camera.main(driver_dfs[focused_driver], driver_objs[focused_driver], render_settings["max_cam_distance"])

    if render_settings["should_render"]:
        print("Starting Rendering...")
        render_animation.main(render_settings, len(driver_dfs[focused_driver]))
    else:
        bpy.context.scene.frame_end = max([len(driver_dfs[driver]) for driver in driver_dfs])
        bpy.context.scene.render.fps = fps
        print("should_render is set to false, skipping rendering...")

    print("End script")


if __name__ == "__main__":
    if len(sys.argv) < 5:
        print("Usage: blender --python render.py -- <path_to_yaml>")
        sys.exit(1)

    main(sys.argv[4])
