import os
import sys

import bpy
import yaml
from utils.project_structure import PYTHON_PROJECT_ROOT

MAIN_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
PYTHON_PROJECT_ROOT = os.path.join(MAIN_PROJECT_ROOT, "py")
sys.path.append(PYTHON_PROJECT_ROOT)

import add_camera
import add_driver_objects
import add_sun
import add_track
import render_animation
from utils.read_yaml import read_yaml


def read_from_yaml():
    with open("conf.yaml", "r") as file:
        config = yaml.safe_load(file)

    year = config["year"]
    track = config["track"]
    fps = config["render"]["fps"]

    assert isinstance(year, int)
    assert isinstance(track, str)
    assert isinstance(fps, int)

    drivers = []
    for driver in config["drivers"]:
        name = driver["name"]
        color = driver["color"]

        assert isinstance(name, str)
        assert isinstance(color, str)

        drivers.append((name, color))

    print("Received Config:")
    print(f"    Year: {year}")
    print(f"    Track: {track}")
    print(f"    FPS: {fps}")
    print("Drivers:")
    for driver in drivers:
        print("    " + str(driver))

    render_settings = config["render"]

    return year, track, fps, drivers, render_settings


# we already have loaded the track data and the car data for all cars
# on this year and track, now, we just need the cars to render
def main(yaml_path):
    year, track, fps, drivers, config = read_yaml(yaml_path)

    bpy.data.collections.remove(bpy.data.collections["Collection"], do_unlink=True)
    bpy.context.scene.world.node_tree.nodes["Background"].inputs[0].default_value = (0.6, 0.6, 0.6, 1)
    add_sun.main()

    print("Adding Track...")
    add_track.main(str(year), track)

    print("Adding Drivers...")
    focused_driver = drivers[0][0]  # the camera driver is just the first listed
    driver_objs, driver_dfs = add_driver_objects.main(str(year), track, str(fps), drivers)

    add_camera.main(driver_dfs[focused_driver], driver_objs[focused_driver])

    bpy.ops.file.find_missing_files(directory="resources/cars/formula-1-2024-generic/textures")

    render_settings = config["render"]
    if render_settings["should_render"]:
        print("Starting Rendering...")
        render_animation.main(render_settings, len(driver_dfs[focused_driver]))
    else:
        print("should_render is set to false, skipping rendering...")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python render.py <path_to_yaml>")
        sys.exit(1)

    main(sys.argv[1])
