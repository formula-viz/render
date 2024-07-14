import os
import sys

import bpy
import yaml
from fastf1 import plotting

script_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(script_path)

import add_drivers
import load_sequence


def read_from_yaml():
    with open("conf.yaml", "r") as file:
        config = yaml.safe_load(file)

    year = config["year"]
    track = config["track"]
    fps = config["render"]["fps"]

    assert isinstance(year, int)
    assert isinstance(track, str)
    assert isinstance(fps, int)

    drivers = []
    for driver in config["drivers"]:
        name = driver["name"]
        color = driver["color"]

        assert isinstance(name, str)
        assert isinstance(color, str)

        drivers.append((name, color))

    print("Received Config:")
    print(f"    Year: {year}")
    print(f"    Track: {track}")
    print(f"    FPS: {fps}")
    print("Drivers:")
    for driver in drivers:
        print("    " + str(driver))

    render_settings = config["render"]

    return year, track, fps, drivers, render_settings


def set_background(num_frames):
    file_path = "resources/backgrounds/background1.jpeg"
    image_strip = bpy.context.scene.sequence_editor.sequences.new_image(
        name="BackgroundImage", filepath=file_path, channel=1, frame_start=1
    )
    image_strip.frame_final_duration = num_frames

    image_strip.transform.scale_x = 0.64
    image_strip.transform.scale_y = 0.55


# list in the form of HAM, VER, etc.
def main():
    year, track, fps, drivers, render_settings = read_from_yaml()

    num_frames = load_sequence.main()

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
    bpy.ops.render.render(animation=True)


main()
