import os
import sys

import yaml

script_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(script_path)

import add_camera
import add_driver_objects
import add_sun
import add_track


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

    return year, track, fps, drivers


# we already have loaded the track data and the car data for all cars
# on this year and track, now, we just need the cars to render
def main():
    year, track, fps, drivers = read_from_yaml()

    bpy.data.collections.remove(bpy.data.collections["Collection"], do_unlink=True)
    bpy.context.scene.world.node_tree.nodes["Background"].inputs[0].default_value = (0.6, 0.6, 0.6, 1)
    add_sun.main()

    add_track.main(str(year), track)

    focused_driver = drivers[0][0]  # the camera driver is just the first listed
    driver_objs, driver_dfs = add_driver_objects.main(str(year), track, str(fps), drivers)

    add_camera.main(driver_dfs[focused_driver], driver_objs[focused_driver])

    bpy.context.scene.frame_end = len(driver_dfs[focused_driver])
    bpy.context.scene.render.fps = fps

    bpy.ops.file.find_missing_files(directory="resources/cars/formula-1-2024-generic/textures")

    render(output_file)
