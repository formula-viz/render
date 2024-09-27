import json
import logging
import sys

import bpy

logger = logging.getLogger(__name__)

import add_drivers
import load_sequence
from utils.project_structure import Resources


def set_background(num_frames):
    image_strip = bpy.context.scene.sequence_editor.sequences.new_image(
        name="BackgroundImage", filepath=Resources.get_background_image_path(), channel=1, frame_start=1
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
        name="BackgroundMusic", filepath=Resources.get_background_music_path(), channel=3, frame_start=1
    )
    audio_strip.frame_final_duration = total_frames
    return audio_strip


def main(inp):
    print("Enter post_render.py")
    config = json.loads(inp)

    num_frames = load_sequence.main()
    if num_frames == 0:
        num_frames = 100
        print(f"No frames, assuming this is a run for testing, setting num_frames to {num_frames}")

    add_music(num_frames)
    set_background(num_frames)
    add_drivers.main(config["drivers"], num_frames, config["render"]["is_4k"], config["track"], str(config["year"]))

    bpy.context.scene.render.use_sequencer = True

    bpy.context.scene.render.image_settings.file_format = "FFMPEG"
    bpy.context.scene.render.ffmpeg.format = "MPEG4"
    bpy.context.scene.render.filepath = f"output/{config["render"]["output"]}"

    if config["render"]["is_4k"]:
        bpy.context.scene.render.resolution_x = 3840
        bpy.context.scene.render.resolution_y = 2160
    else:
        bpy.context.scene.render.resolution_x = 1920
        bpy.context.scene.render.resolution_y = 1080

    bpy.context.scene.render.fps = config["render"]["fps"]
    bpy.context.scene.frame_end = num_frames

    # outro_frames_length = fps * 8
    # add_outro_image(num_frames, outro_frames_length)
    # bpy.context.scene.frame_end = num_frames + outro_frames_length

    if config["render"]["should_render"]:
        bpy.ops.render.render(animation=True)
        print("Exiting post_render.py")
        bpy.ops.wm.quit_blender()
    else:
        logger.info("should_render is set to false, skipping rendering...")


if __name__ == "__main__":
    main(sys.argv[-1])
