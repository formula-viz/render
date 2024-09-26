import json
import logging
import sys

import bpy

logger = logging.getLogger(__name__)

import add_drivers
import load_sequence
from utils.config import Config
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


def gen_sample_config_for_render_test():
    yaml_dict = {
        "track": "SIN",
        "year": "2024",
        "render": {
            "should_render": False,
            "validate_render": False,
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


def main(inp):
    print("Enter post_render.py")
    if inp == "testing":
        config = gen_sample_config_for_render_test()
        num_frames = 100
    elif inp == "end-to-end":
        config = gen_sample_config_for_render_test()
        num_frames = load_sequence.main()
    else:
        config = Config.from_dict(json.loads(inp))
        num_frames = load_sequence.main()

    add_music(num_frames)
    set_background(num_frames)
    add_drivers.main(config.drivers, num_frames, config.is_4k, config.track, str(config.year))

    bpy.context.scene.render.use_sequencer = True

    bpy.context.scene.render.image_settings.file_format = "FFMPEG"
    bpy.context.scene.render.ffmpeg.format = "MPEG4"
    bpy.context.scene.render.filepath = f"output/{config.output}"

    if config.is_4k:
        bpy.context.scene.render.resolution_x = 3840
        bpy.context.scene.render.resolution_y = 2160
    else:
        bpy.context.scene.render.resolution_x = 1920
        bpy.context.scene.render.resolution_y = 1080

    bpy.context.scene.render.fps = config.fps
    bpy.context.scene.frame_end = num_frames

    # outro_frames_length = fps * 8
    # add_outro_image(num_frames, outro_frames_length)
    # bpy.context.scene.frame_end = num_frames + outro_frames_length

    if config.should_render:
        bpy.ops.render.render(animation=True)
    else:
        logger.info("should_render is set to false, skipping rendering...")

    print("Exiting post_render.py")


if __name__ == "__main__":
    main(sys.argv[-1])
