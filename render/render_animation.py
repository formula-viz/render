import os

import bpy


def configure_gpu(render_settings):
    if not bpy.context.preferences.addons.get("cycles"):
        bpy.ops.preferences.addon_enable(module="cycles")

    bpy.context.scene.render.engine = "CYCLES"
    bpy.context.scene.cycles.device = "GPU"
    bpy.context.preferences.addons["cycles"].preferences.compute_device_type = "CUDA"

    bpy.context.preferences.addons["cycles"].preferences.get_devices()
    for d in bpy.context.preferences.addons["cycles"].preferences.devices:
        if "nvidia" in d["name"].lower():
            d["use"] = 1
            print(f"Using GPU: {d['name']}")

    bpy.context.scene.cycles.use_adaptive_sampling = render_settings["adaptive_sampling"]


# render settings will be sent in as a dict from yaml
def main(render_settings, num_frames):
    if not render_settings["should_render"]:
        print("Set to not render, skipping rendering...")

    print(f"Starting Rendering of {num_frames} with...")
    print(render_settings)
    configure_gpu(render_settings)

    bpy.context.scene.frame_end = num_frames
    bpy.context.scene.frame_end = 50
    bpy.context.scene.render.fps = render_settings["fps"]

    bpy.context.scene.cycles.samples = render_settings["samples"]

    bpy.context.scene.cycles.use_denoising = False

    if render_settings["is_4k"]:
        bpy.context.scene.render.resolution_x = 3840
        bpy.context.scene.render.resolution_y = 2160

        # it is better to use 1 tile because gpu has 12GB of memory
        bpy.context.scene.cycles.tile_x = 3840
        bpy.context.scene.cycles.tile_y = 2160
    else:
        bpy.context.scene.render.resolution_x = 1920
        bpy.context.scene.render.resolution_y = 1080

        bpy.context.scene.cycles.tile_x = 1920
        bpy.context.scene.cycles.tile_y = 1080


    # we want to render as a sequence of pngs so that we can add a background in vse
    bpy.context.scene.render.film_transparent = True
    # Set output format to PNG with RGBA channels
    bpy.context.scene.render.image_settings.file_format = "PNG"
    bpy.context.scene.render.image_settings.color_mode = "RGBA"
    # first, let's delete the tmp folder to wipe it
    os.system("rm -rf tmp")
    os.system("mkdir tmp")
    bpy.context.scene.render.filepath = "tmp/frame_"

    bpy.ops.render.render(animation=True)
