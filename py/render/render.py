import json
import sys

# print python path
print("Python path:")
print(sys.path)


import add_camera
import add_driver_objects
import add_indicators
import add_sun
import add_track
import bpy
import load_driver_data
import load_track_data
import render_animation
from utils.config import Config


def gen_sample_config_for_render_test():
    yaml_dict = {
        "track": "SIN",
        "year": "2024",
        "render": {
            "should_render": False,
            "validate_render": True,
            "fps": 30,
            "samples": 32,
            "adaptive_sampling": True,
            "is_4k": True,
            "output": "output.mp4",
            "max_cam_distance": 70,
        },
        "drivers": [
            {"name": "TSU", "color": "#00FF00"},
            {"name": "RIC", "color": "#0000FF"},
        ],
    }

    return Config.from_dict(yaml_dict)


# we already have loaded the track data and the car data for all cars
# on this year and track, now, we just need the cars to render
def main(inp):
    print("Enter render.py")
    if inp == "testing":
        config = gen_sample_config_for_render_test()
    else:
        config = Config.from_dict(json.loads(inp))

    start_buffer_frames = 45
    end_buffer_frames = 75

    bpy.data.collections.remove(bpy.data.collections["Collection"], do_unlink=True)
    add_sun.main()

    print("Loading Track Data...")
    inner_points, outer_points, inner_curb_points, outer_curb_points = load_track_data.main(config.year, config.track)

    print("Adding Track...")
    add_track.main(inner_points, outer_points, inner_curb_points, outer_curb_points)

    print("Adding Drivers...")
    focused_driver = config.drivers[0][0]  # the camera driver is just the first listed
    driver_dfs, start_finish_line_idx = load_driver_data.main(
        config.year, config.track, config.fps, start_buffer_frames, end_buffer_frames, inner_points, outer_points
    )
    driver_objs = add_driver_objects.main(driver_dfs, config.drivers)

    print("Adding Indicators...")
    add_indicators.main(inner_curb_points, outer_curb_points, start_finish_line_idx)

    add_camera.main(
        driver_dfs[focused_driver],
        driver_objs[focused_driver],
        config.max_cam_distance,
        start_buffer_frames,
        end_buffer_frames,
    )

    if config.should_render:
        print("Starting Rendering...")
        render_animation.main(config, len(driver_dfs[focused_driver]))
    else:
        # for driver in drivers not all ~20 in the lineup
        bpy.context.scene.frame_end = min([len(driver_dfs[driver_abbrev]) for (driver_abbrev, _) in config.drivers]) - 1
        bpy.context.scene.render.fps = config.fps
        print("should_render is set to false, skipping rendering...")

    print("Exiting render.py")


if __name__ == "__main__":
    main(sys.argv[-1])
