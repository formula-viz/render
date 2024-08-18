import os
import sys

import bpy

MAIN_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
PYTHON_SCRIPTS_ROOT = os.path.join(MAIN_PROJECT_ROOT, "py")
sys.path.append(MAIN_PROJECT_ROOT)
sys.path.append(PYTHON_SCRIPTS_ROOT)
sys.path.append(os.path.dirname(os.path.realpath(__file__)))

import logging

logger = logging.getLogger(__name__)

import add_drivers
import load_sequence
from utils.project_structure import (BACKGROUND_ONE_PATH,
                                     get_background_music_path)
from utils.read_yaml import read_yaml


def set_background(num_frames):
    image_strip = bpy.context.scene.sequence_editor.sequences.new_image(
        name="BackgroundImage", filepath=BACKGROUND_ONE_PATH, channel=1, frame_start=1
    )
    image_strip.frame_final_duration = num_frames

    image_strip.transform.scale_x = 0.64
    image_strip.transform.scale_y = 0.55


def add_outro_image(num_frames, outro_frames_length):
    image_strip = bpy.context.scene.sequence_editor.sequences.new_image(
        name="OverlayImage", filepath="resources/outros/credit.png", channel=1, frame_start=num_frames + 1
    )

    image_strip.frame_final_duration = num_frames + outro_frames_length
    return image_strip


def add_music(total_frames):
    audio_strip = bpy.context.scene.sequence_editor.sequences.new_sound(
        name="BackgroundMusic", filepath=get_background_music_path(), channel=3, frame_start=1
    )
    audio_strip.frame_final_duration = total_frames
    return audio_strip


# list in the form of HAM, VER, etc.
def main(yaml_path, frames_dir):
    year, track, fps, drivers, config = read_yaml(yaml_path)
    render_settings = config["render"]

    num_frames = load_sequence.main(frames_dir)

    add_music(num_frames)
    set_background(num_frames)
    add_drivers.main(drivers, num_frames, render_settings["is_4k"], track, str(year))

    bpy.context.scene.render.use_sequencer = True

    bpy.context.scene.render.image_settings.file_format = "FFMPEG"
    bpy.context.scene.render.ffmpeg.format = "MPEG4"
    bpy.context.scene.render.filepath = f"output/{render_settings['output']}"

    if render_settings["is_4k"]:
        bpy.context.scene.render.resolution_x = 3840
        bpy.context.scene.render.resolution_y = 2160
    else:
        bpy.context.scene.render.resolution_x = 1920
        bpy.context.scene.render.resolution_y = 1080

    bpy.context.scene.render.fps = fps
    bpy.context.scene.frame_end = num_frames

    # outro_frames_length = fps * 8
    # add_outro_image(num_frames, outro_frames_length)
    # bpy.context.scene.frame_end = num_frames + outro_frames_length

    if render_settings["should_render"]:
        bpy.ops.render.render(animation=True)
    else:
        logger.info("should_render is set to false, skipping rendering...")


if __name__ == "__main__":
    if len(sys.argv) < 5:
        print("Usage: blender --python post_render.py -- <path_to_yaml> <path_to_frames>")
        sys.exit(1)

    yaml_path = sys.argv[4]
    frames_dir = sys.argv[5]

    main(yaml_path, frames_dir)
