import os
import sys

import bpy
import fastf1

script_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(script_path)

from modules.add_camera import add_camera
from modules.configure_sun import configure_sun
from modules.create_driver_fbx import create_drivers
from modules.delete_default_collection import delete_default_collection
from modules.generate_track import generate_track


def foo(year, track, session, drivers):

    delete_default_collection()
    configure_sun()
    generate_track(year, track)

    car_camera_file_loc = f"https://raw.githubusercontent.com/formula-viz/car-and-camera-data-process/main/animation-data-package/{year}_{track}_{session}_{'_'.join(drivers)}"
    add_camera(car_camera_file_loc)

    session = fastf1.get_session(year, track, session)
    session.load()

    num_frames = create_drivers(drivers, session)

    bpy.context.scene.frame_end = num_frames
    bpy.context.scene.render.fps = 60  # the frames from camera and car data process assume we are using 60 fps


if __name__ == "__main__":
    # a run is uniquely identified by: year, track, session, [driver:]
    if len(sys.argv) < 6:  # for now we force at least 2 drivers
        print("Usage: python entry.py <year> <track> <session> <driver1> <driver2> ...")
        sys.exit(1)

    # arguments start at 4 because we have blender --python entry.py -- <year> <track> <session> <driver1> <driver2> ...
    year = int(sys.argv[4])
    track = sys.argv[5]
    session = sys.argv[6]
    drivers = sys.argv[7:]

    foo(year, track, session, drivers)
