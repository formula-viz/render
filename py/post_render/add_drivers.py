import json

import bpy
from utils.colors import hex_to_blender_rgb
from utils.project_structure import DriverData, Resources


# currently configured for 2 driver videos, where the drivers are either is_left or !is_left
class DriverGraphic:
    # where start_channel is the lowest channel number
    def __init__(
        self,
        driver_abbrev: str,
        driver_hex_color: str,
        num_frames: int,
        driver_time: str,
        is_4k: bool,
        start_channel: int,
        is_left: bool,
    ):
        self.driver_abbrev = driver_abbrev
        self.driver_hex_color = driver_hex_color
        self.num_frames = num_frames
        self.driver_time = driver_time
        self.is_4k = is_4k
        self.start_channel = start_channel
        self.is_left = is_left

        image_strip = self._add_driver_image()
        color_strip = self._add_color_strip()
        time_strip = self._add_time_strip()

        self._scale_strips(image_strip, color_strip, time_strip)
        self._position_strips(image_strip, color_strip, time_strip)

    def _scale_strips(self, image_strip, color_strip, time_strip):
        if self.is_4k:
            image_strip.transform.scale_x = 0.6
            image_strip.transform.scale_y = 0.6

            color_strip.transform.scale_x = 0.13
            color_strip.transform.scale_y = 0.015

            time_strip.font_size = 60
        else:
            # TODO: This may be incorrect for 1920x1080
            image_strip.transform.scale_x = 0.3
            image_strip.transform.scale_y = 0.3

            color_strip.transform.scale_x = 0.13
            color_strip.transform.scale_y = 0.01

            time_strip.font_size = 30

    def _position_strips(self, image_strip, color_strip, time_strip):
        if self.is_4k:
            image_strip.transform.offset_x = 1600
            image_strip.transform.offset_y = -650

            color_strip.transform.offset_x = 1615
            color_strip.transform.offset_y = -900

            time_strip.location[0] = 0.08
            time_strip.location[1] = 0.05

            # we just overwrite the above values if is_left
            if self.is_left:
                image_strip.use_flip_x = True
                color_strip.use_flip_x = True

                time_strip.location[0] = 0.92
        else:
            image_strip.transform.offset_x = 800
            image_strip.transform.offset_y = -328

            color_strip.transform.offset_x = 808
            color_strip.transform.offset_y = -457

            time_strip.location[0] = 0.08
            time_strip.location[1] = 0.05

            if self.is_left:
                image_strip.use_flip_x = True
                color_strip.use_flip_x = True

                time_strip.location[0] = 0.92

    def _add_driver_image(self):
        loc = DriverData.get_driver_image_path(self.driver_abbrev)
        image_strip = bpy.context.scene.sequence_editor.sequences.new_image(
            name=self.driver_abbrev + "_OverlayImage", filepath=loc, channel=self.start_channel, frame_start=1
        )

        image_strip.frame_final_duration = self.num_frames
        return image_strip

    def _add_color_strip(self):
        r, g, b = hex_to_blender_rgb(self.driver_hex_color)

        print("self.num_frames", self.num_frames)

        color_strip = bpy.context.scene.sequence_editor.sequences.new_effect(
            name=self.driver_abbrev + "_Color",
            type="COLOR",
            channel=self.start_channel + 1,
            frame_start=1,
            frame_end=self.num_frames + 1,
        )

        color_strip.color = (r, g, b)
        return color_strip

    def _add_time_strip(self):
        name_strip = bpy.context.scene.sequence_editor.sequences.new_effect(
            name=self.driver_abbrev + "_Text",
            type="TEXT",
            channel=self.start_channel + 2,
            frame_start=1,
            frame_end=self.num_frames + 1,
        )
        name_strip.text = self.driver_time
        name_strip.font = bpy.data.fonts.load(Resources.get_main_font())

        return name_strip


def load_times_dict(year: str, track: str):
    loc = DriverData.get_driver_times_path(year, track)
    with open(loc, "r") as file:
        retrieved_driver_times = json.load(file)

    return retrieved_driver_times


# [(name, color), ...]
def main(drivers, num_frames: int, is_4k: bool, track: str, year: str):
    driver_times = load_times_dict(year, track)

    # for now, we just assume that there will be 2 drivers
    num_strips = 3
    main_start = 5

    left_driver = drivers[0]
    DriverGraphic(left_driver[0], left_driver[1], num_frames, driver_times[left_driver[0]], is_4k, main_start, True)

    right_driver = drivers[1]
    DriverGraphic(
        right_driver[0],
        right_driver[1],
        num_frames,
        driver_times[right_driver[0]],
        is_4k,
        main_start + num_strips,
        False,
    )
