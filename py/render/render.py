from abc import ABC, abstractmethod

import bpy # pyright: ignore
from render_funcs import (add_camera, add_driver_objects, add_indicators,
                          add_sun, add_track, add_status_track, load_driver_data,
                          load_track_data, render_animation, car_rankings)
from utils.colors import get_rest_of_field_colors, get_head_to_head_colors
from utils.logger import log_info


class AbstractRenderer(ABC):
    def __init__(self, config):
        self.config = config

    @abstractmethod
    def setup_track(self):
        bpy.data.collections.remove(bpy.data.collections["Collection"], do_unlink=True)  # default collection
        add_sun.main()
        self.track_data = load_track_data.main(self.config["year"], self.config["track"])
        add_track.main(self.track_data)

    @abstractmethod
    def add_drivers(self):
        pass

    @abstractmethod
    def add_camera(self):
        pass

    def configure_widgets(self):
        add_status_track.main(self.track_data, self.camera_obj, self.start_finish_line_idx, self.driver_dfs[self.focused_driver])

    # this should be the same for all jobs
    def trigger_render(self):
        log_info("Starting Rendering...")
        render_animation.main(self.config, len(self.driver_dfs[self.focused_driver]))

    # this has to be a separate function because the car data must be loaded before in order to get an
    # accurate estimation of the location of the start finish line
    # should be the same for all renders so it is not abstract
    def add_indicators(self):
        add_indicators.main(
            self.track_data.inner_curb_points, self.track_data.outer_curb_points, self.start_finish_line_idx
        )

    def render(self):
        """Main process which should be called"""
        self.setup_track()  # track_data is a dependency for later operations
        self.add_drivers()
        self.add_indicators()
        self.add_camera()
        self.configure_widgets()
        car_rankings.main(self.track_data, self.start_finish_line_idx, self.driver_dfs, self.config)
        self.trigger_render()


class HeadToHeadRenderer(AbstractRenderer):
    def setup_track(self):
        super().setup_track()

    def add_drivers(self):
        self.driver_dfs, self.start_finish_line_idx = load_driver_data.main(self.config, self.track_data)
        colors = get_head_to_head_colors(*self.config["drivers"])

        self.driver_objs = add_driver_objects.main(self.driver_dfs, self.config["drivers"], colors)

    def add_camera(self):
        self.focused_driver = self.config["drivers"][0]  # in head to head, focus on the first driver
        self.camera_obj = add_camera.main(
            self.driver_dfs[self.focused_driver],
            self.driver_objs[self.focused_driver],
            self.config["render"]["max_cam_distance"],
            self.config["render"]["start_buffer_frames"],
            self.config["render"]["end_buffer_frames"],
            self.config["render"]["is_mobile"]
        )


class RestOfFieldRenderer(AbstractRenderer):
    def setup_track(self):
        super().setup_track()

    def add_drivers(self):
        self.driver_dfs, self.start_finish_line_idx = load_driver_data.main(self.config, self.track_data)
        colors = get_rest_of_field_colors()

        # for now, gold driver is just the first driver listed in drivers
        focused_driver = self.config["drivers"][0]
        drivers = [driver for driver in self.driver_dfs.keys() if driver != focused_driver]
        drivers.insert(0, focused_driver)

        self.driver_objs = add_driver_objects.main(self.driver_dfs, drivers, colors)

    def add_camera(self):
        self.focused_driver = self.config["drivers"][0]
        self.camera_obj = add_camera.main(
            self.driver_dfs[self.focused_driver],
            self.driver_objs[self.focused_driver],
            self.config["render"]["max_cam_distance"],
            self.config["render"]["start_buffer_frames"],
            self.config["render"]["end_buffer_frames"],
            self.config["render"]["is_mobile"]
        )
