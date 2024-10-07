from abc import ABC, abstractmethod

import bpy
from post_render_funcs import add_drivers, load_sequence
from utils.colors import (GOLD_RGB, get_head_to_head_colors,
                          get_scene_bg_color, rgb_to_hex)
from utils.project_structure import Resources


class AbstractPostRenderer(ABC):
    def __init__(self, config):
        self.config = config

    @abstractmethod
    def load_sequence(self):
        self.num_frames = load_sequence.main()
        if self.num_frames == 0:
            self.num_frames = 100
            print(f"No frames, assuming this is a run for testing, setting num_frames to {self.num_frames}")

    @abstractmethod
    def add_music(self):
        bpy.context.scene.render.ffmpeg.audio_codec = "AAC"
        bpy.context.scene.render.ffmpeg.audio_bitrate = 192  # Set bitrate to 192 kbps
        bpy.context.scene.render.ffmpeg.audio_channels = "STEREO"

        audio_strip = bpy.context.scene.sequence_editor.sequences.new_sound(
            name="BackgroundMusic", filepath=Resources.get_background_music_path(), channel=3, frame_start=1
        )
        audio_strip.frame_final_duration = self.num_frames

    @abstractmethod
    def set_background(self):
        color_strip = bpy.context.scene.sequence_editor.sequences.new_effect(
            name="BackgroundColor",
            type="COLOR",
            channel=1,
            frame_start=1,
            frame_end=self.num_frames,
        )
        color_strip.color = get_scene_bg_color()

        # image_strip = bpy.context.scene.sequence_editor.sequences.new_image(
        #     name="BackgroundImage", filepath=Resources.get_background_image_path(), channel=1, frame_start=1
        # )
        # image_strip.frame_final_duration = self.num_frames
        #
        # image_strip.transform.scale_x = 0.64
        # image_strip.transform.scale_y = 0.55

    @abstractmethod
    def add_visuals(self):
        pass

    @abstractmethod
    def trigger_render(self):
        bpy.context.scene.render.use_sequencer = True

        bpy.context.scene.render.image_settings.file_format = "FFMPEG"
        bpy.context.scene.render.ffmpeg.format = "MPEG4"
        bpy.context.scene.render.filepath = f"output/{self.config['render']['output']}"

        bpy.context.scene.render.resolution_x = 3840
        bpy.context.scene.render.resolution_y = 2160

        bpy.context.scene.render.fps = self.config["render"]["fps"]
        bpy.context.scene.frame_end = self.num_frames

        if self.config["pipeline"]["preview_mode"]:
            print("In preview mode, skipping rendering...")
        else:
            bpy.ops.render.render(animation=True)
            print("Exiting post_render.py")
            bpy.ops.wm.quit_blender()

    def post_render(self):
        self.load_sequence()
        self.add_music()
        self.set_background()
        self.add_visuals()
        self.trigger_render()


# I am going to set such that this will always be rendered in 4k
class HeadToHeadPostRenderer(AbstractPostRenderer):
    def load_sequence(self):
        super().load_sequence()

    def add_music(self):
        super().add_music()

    def set_background(self):
        super().set_background()

    def add_visuals(self):
        driver_times = add_drivers.load_times_dict(self.config["year"], self.config["track"])
        driver_colors = get_head_to_head_colors(*self.config["drivers"])

        num_strips = 3
        main_start = 5

        add_drivers.DriverGraphic(
            self.config["drivers"][0],
            driver_colors[0],
            self.num_frames,
            driver_times[self.config["drivers"][0]],
            self.config["render"]["is_4k"],
            main_start,
            True,
        )

        add_drivers.DriverGraphic(
            self.config["drivers"][1],
            driver_colors[1],
            self.num_frames,
            driver_times[self.config["drivers"][1]],
            self.config["render"]["is_4k"],
            main_start + num_strips,
            False,
        )

    def trigger_render(self):
        super().trigger_render()


class RestOfFieldPostRenderer(AbstractPostRenderer):
    def load_sequence(self):
        return super().load_sequence()

    def add_music(self):
        return super().add_music()

    def set_background(self):
        return super().set_background()

    def add_visuals(self):
        driver_times = add_drivers.load_times_dict(self.config["year"], self.config["track"])
        gold_hex = rgb_to_hex(GOLD_RGB)

        main_start = 5
        add_drivers.DriverGraphic(
            self.config["drivers"][0],
            gold_hex,
            self.num_frames,
            driver_times[self.config["drivers"][0]],
            self.config["render"]["is_4k"],
            main_start,
            True,
        )

    def trigger_render(self):
        return super().trigger_render()
