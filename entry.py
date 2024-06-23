import os
import sys

import bpy
import fastf1

script_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(script_path)

from modules.add_camera import add_camera
from modules.configure_sun import configure_sun
from modules.create_drivers import create_drivers_and_cam
from modules.delete_default_collection import delete_default_collection
from modules.generate_track import generate_track


def foo(year, track, session, drivers):

    delete_default_collection()
    configure_sun()
    generate_track(year, track)

    session = fastf1.get_session(year, track, session)
    session.load()

    colors = [(1, 0, 0), (0, 0, 1)]
    num_frames, df_for_cam, driver_obj = create_drivers_and_cam(drivers, colors, session)
    add_camera(df_for_cam, driver_obj)

    bpy.context.scene.frame_end = num_frames
    bpy.context.scene.render.fps = 60  # the frames from camera and car data process assume we are using 60 fps

    bpy.ops.file.find_missing_files(directory="formula-1-2024-generic/textures")


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
