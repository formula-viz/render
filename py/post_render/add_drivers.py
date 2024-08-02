import json

import bpy
from fastf1 import plotting
from utils.project_structure import (FORMULA_ONE_REGULAR_FONT_PATH,
                                     get_driver_image_path,
                                     get_driver_times_path)


def add_driver_image(driver_abbrev, num_frames, channel):
    loc = get_driver_image_path(driver_abbrev)
    image_strip = bpy.context.scene.sequence_editor.sequences.new_image(
        name="OverlayImage", filepath=loc, channel=channel, frame_start=1
    )

    image_strip.frame_final_duration = num_frames
    return image_strip


def load_times_dict(year: str, track: str):
    loc = get_driver_times_path(year, track)
    with open(loc, "r") as file:
        retrieved_driver_times = json.load(file)

    return retrieved_driver_times


def add_time_strip(driver_abbrev, num_frames, time_str, channel):
    name_strip = bpy.context.scene.sequence_editor.sequences.new_effect(
        name=driver_abbrev + "_Text",
        type="TEXT",
        channel=channel,
        frame_start=1,
        frame_end=num_frames + 1,
    )
    name_strip.text = time_str
    name_strip.font = bpy.data.fonts.load(FORMULA_ONE_REGULAR_FONT_PATH)

    return name_strip


def add_color_strip(driver_abbrev, num_frames, channel):
    color = plotting.DRIVER_COLORS[plotting.DRIVER_TRANSLATE[driver_abbrev]]
    r, g, b = tuple(int(color[i : i + 2], 16) / 255.0 for i in (1, 3, 5))

    color_strip = bpy.context.scene.sequence_editor.sequences.new_effect(
        name="Color", type="COLOR", channel=channel, frame_start=1, frame_end=num_frames + 1
    )

    color_strip.color = (r, g, b)
    return color_strip


# the process for adding the drivers will be different if there are 2 drivers,
# 3 drivers, 4 drivers, etc. the sizes and the positions will change
def add_drivers(driver_a, driver_b, num_frames, is_4k, driver_times):
    image_strip_a = add_driver_image(driver_a, num_frames, 3)
    color_strip_a = add_color_strip(driver_a, num_frames, 4)
    time_strip_a = add_time_strip(driver_a, num_frames, driver_times[driver_a], 5)

    image_strip_b = add_driver_image(driver_b, num_frames, 6)
    color_strip_b = add_color_strip(driver_b, num_frames, 7)
    time_strip_b = add_time_strip(driver_b, num_frames, driver_times[driver_b], 8)

    if is_4k:

        def configure_4k_images():
            # first set the scale based on resolution
            image_strip_a.transform.scale_x = 0.6
            image_strip_a.transform.scale_y = 0.6

            image_strip_b.transform.scale_x = 0.6
            image_strip_b.transform.scale_y = 0.6

            # now for the image locations
            # the negative values indicate left or below
            image_strip_a.transform.offset_x = 1600
            # for the a image on the left, we will mirror flip x,
            # this way both drivers will have their shoulders faced inward
            image_strip_a.use_flip_x = True
            image_strip_a.transform.offset_y = -650

            image_strip_b.transform.offset_x = 1600
            image_strip_b.transform.offset_y = -650

        def configure_4k_colors():
            # set scale
            color_strip_a.transform.scale_x = 0.13
            color_strip_a.transform.scale_y = 0.015

            color_strip_b.transform.scale_x = 0.13
            color_strip_b.transform.scale_y = 0.015

            # set locations
            color_strip_a.transform.offset_x = -1615
            color_strip_a.transform.offset_y = -900

            color_strip_b.transform.offset_x = 1615
            color_strip_b.transform.offset_y = -900

        def configure_4k_times():
            # now for the text strip locations
            time_strip_a.location[0] = 0.08
            time_strip_a.location[1] = 0.05

            time_strip_b.location[0] = 0.92
            time_strip_b.location[1] = 0.05

            # we need to set the font size for the 4k resolution
            time_strip_a.font_size = 60
            time_strip_b.font_size = 60

        configure_4k_images()
        configure_4k_colors()
        configure_4k_times()

    else:

        def configure_1920_images():
            # first set the scale based on resolution
            image_strip_a.transform.scale_x = 0.3
            image_strip_a.transform.scale_y = 0.3

            image_strip_b.transform.scale_x = 0.3
            image_strip_b.transform.scale_y = 0.3

            # now for the image locations
            # the negative values indicate left or below
            image_strip_a.transform.offset_x = 800
            # for the a image on the left, we will mirror flip x,
            # this way both drivers will have their shoulders faced inward
            image_strip_a.use_flip_x = True
            image_strip_a.transform.offset_y = -328

            image_strip_b.transform.offset_x = 800
            image_strip_b.transform.offset_y = -328

        def configure_1920_colors():
            # set scale
            color_strip_a.transform.scale_x = 0.13
            color_strip_a.transform.scale_y = 0.01

            color_strip_b.transform.scale_x = 0.13
            color_strip_b.transform.scale_y = 0.01

            # set locations
            color_strip_a.transform.offset_x = -808
            color_strip_a.transform.offset_y = -457

            color_strip_b.transform.offset_x = 808
            color_strip_b.transform.offset_y = -457

        def configure_1920_times():
            # now for the text strip locations
            time_strip_a.location[0] = 0.08
            time_strip_a.location[1] = 0.05

            time_strip_b.location[0] = 0.92
            time_strip_b.location[1] = 0.05

            # we need to set the font size for the 4k resolution
            time_strip_a.font_size = 30
            time_strip_b.font_size = 30

        configure_1920_images()
        configure_1920_colors()
        configure_1920_times()


# [(name, color), ...]
def main(drivers, num_frames: int, is_4k: bool, track: str, year: str):
    driver_times = load_times_dict(year, track)

    if len(drivers) == 2:
        add_drivers(drivers[0][0], drivers[1][0], num_frames, is_4k, driver_times)
