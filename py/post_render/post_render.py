import json
import sys
from abc import ABC, abstractmethod

import bpy
from post_render_funcs import add_drivers, load_sequence
from utils.project_structure import Resources


class AbstractPostRenderer(ABC):
    def __init__(self, config):
        self.config = config

    @abstractmethod
    def load_sequence(self):
        pass

    @abstractmethod
    def add_music(self):
        pass

    @abstractmethod
    def set_background(self):
        pass

    @abstractmethod
    def add_visuals(self):
        pass

    @abstractmethod
    def trigger_render(self):
        pass

    def post_render(self):
        self.load_sequence()
        self.add_music()
        self.set_background()
        self.add_visuals()
        self.trigger_render()


# I am going to set such that this will always be rendered in 4k
class HeadToHeadPostRenderer(AbstractPostRenderer):
    def load_sequence(self):
        self.num_frames = load_sequence.main()
        if self.num_frames == 0:
            self.num_frames = 100
            print(f"No frames, assuming this is a run for testing, setting num_frames to {self.num_frames}")

    def add_music(self):
        bpy.context.scene.render.ffmpeg.audio_codec = "AAC"
        bpy.context.scene.render.ffmpeg.audio_bitrate = 192  # Set bitrate to 192 kbps
        bpy.context.scene.render.ffmpeg.audio_channels = "STEREO"

        audio_strip = bpy.context.scene.sequence_editor.sequences.new_sound(
            name="BackgroundMusic", filepath=Resources.get_background_music_path(), channel=3, frame_start=1
        )
        audio_strip.frame_final_duration = self.num_frames

    def set_background(self):
        image_strip = bpy.context.scene.sequence_editor.sequences.new_image(
            name="BackgroundImage", filepath=Resources.get_background_image_path(), channel=1, frame_start=1
        )
        image_strip.frame_final_duration = self.num_frames

        image_strip.transform.scale_x = 0.64
        image_strip.transform.scale_y = 0.55

    def add_visuals(self):
        add_drivers.main(
            self.config["drivers"],
            self.num_frames,
            self.config["render"]["is_4k"],
            self.config["track"],
            str(self.config["year"]),
        )

    def trigger_render(self):
        bpy.context.scene.render.use_sequencer = True

        bpy.context.scene.render.image_settings.file_format = "FFMPEG"
        bpy.context.scene.render.ffmpeg.format = "MPEG4"
        bpy.context.scene.render.filepath = f"output/{config['render']['output']}"

        bpy.context.scene.render.resolution_x = 3840
        bpy.context.scene.render.resolution_y = 2160

        bpy.context.scene.render.fps = config["render"]["fps"]
        bpy.context.scene.frame_end = self.num_frames

        if self.config["pipeline"]["preview_mode"]:
            print("In preview mode, skipping rendering...")
        else:
            bpy.ops.render.render(animation=True)
            print("Exiting post_render.py")
            bpy.ops.wm.quit_blender()
