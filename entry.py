import os
import sys

import bpy
import fastf1

script_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(script_path)

from modules.add_camera import add_camera
from modules.configure_sun import configure_sun
from modules.create_drivers import create_driver
from modules.delete_default_collection import delete_default_collection
from modules.generate_track import generate_track


def foo(year, track, session, drivers):

    delete_default_collection()
    configure_sun()
    generate_track(year, track)

    session = fastf1.get_session(year, track, session)
    session.load()

    # colors = [(0.072, 0.089, 0.089), (1, 1, 1)]
    colors = [(30, 150, 252), (255, 198, 0)]
    colors = [(r / 255, g / 255, b / 255) for r, g, b in colors]

    driver_tels = [get_driver_tel(driver, session) for driver in drivers]
    # fastf1 interpolates the start/finish line for the car but it is independent of the other cars
    # the problem is that the start/finish will probably be put in a different place for each car.
    # to solve this, we can just take all the drivers we have, average their start/finish line, then
    # make it so that every driver has the same start/finish. This means the start/finish will be different
    # for dif runs on the same track but this does not really matter.
    mean_x = np.mean([tel["X"].iloc[0] for tel in driver_tels])
    mean_y = np.mean([tel["Y"].iloc[0] for tel in driver_tels])
    for tel in driver_tels:
        tel["X"].iloc[0] = mean_x
        tel["Y"].iloc[0] = mean_y

    mean_x = np.mean([tel["X"].iloc[-1] for tel in driver_tels])
    mean_y = np.mean([tel["Y"].iloc[-1] for tel in driver_tels])
    for tel in driver_tels:
        tel["X"].iloc[-1] = mean_x
        tel["Y"].iloc[-1] = mean_y

    num_frames = 0
    for i, (driver, color, tel) in enumerate(zip(drivers, colors, driver_tels)):
        df, driver_obj = create_driver(driver, color, tel)

        # the first driver listed will be the one focused by the camera
        if i == 0:
            add_camera(df, driver_obj)
            num_frames = len(df) # for now, num_frames is just the # of frames in run of focused car


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
