import json
import sys
from abc import ABC, abstractmethod

import add_camera
import add_driver_objects
import add_indicators
import add_sun
import add_track
import bpy
import load_driver_data
import load_track_data
import render_animation


class AbstractRenderer(ABC):
    def __init__(self, config):
        self.config = config

    @abstractmethod
    def setup_track(self):
        pass

    @abstractmethod
    def add_drivers(self):
        pass

    @abstractmethod
    def add_camera(self):
        pass

    # this should be the same for all jobs
    def trigger_render(self):
        if self.config["render"]["should_render"]:
            print("Starting Rendering...")
            render_animation.main(self.config, len(self.driver_dfs[self.focused_driver]))
            print("Exiting render.py")
            bpy.ops.wm.quit_blender()
        else:
            bpy.context.scene.frame_end = (
                min([len(self.driver_dfs[driver_abbrev]) for driver_abbrev in self.config["drivers"]]) - 1
            )
            bpy.context.scene.render.fps = self.config["render"]["fps"]
            print("should_render is set to false, skipping rendering...")

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
        self.trigger_render()


class HeadToHeadRenderer(AbstractRenderer):
    def setup_track(self):
        bpy.data.collections.remove(bpy.data.collections["Collection"], do_unlink=True)  # default collection
        add_sun.main()
        self.track_data = load_track_data.main(self.config["year"], self.config["track"])
        add_track.main(self.track_data)

    def add_drivers(self):
        self.driver_dfs, self.start_finish_line_idx = load_driver_data.main(self.config, self.track_data)
        self.driver_objs = add_driver_objects.main(self.driver_dfs, self.config["drivers"], "head-to-head")

    def add_camera(self):
        focused_driver = self.config["drivers"][0]  # in head to head, focus on the first driver
        add_camera.main(
            self.driver_dfs[focused_driver],
            self.driver_objs[focused_driver],
            self.config["render"]["max_cam_distance"],
            self.config["render"]["start_buffer_frames"],
            self.config["render"]["end_buffer_frames"],
        )


if __name__ == "__main__":
    print("Enter render.py")
    config = json.loads(sys.argv[-1])
    video_type = config["type"]

    if video_type == "head-to-head":
        print("Creating HeadToHeadRenderer...")
        renderer = HeadToHeadRenderer(config)
        renderer.render()
