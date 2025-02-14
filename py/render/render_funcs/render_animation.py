import os

import bpy
from utils.project_structure import get_frames_dir
from utils.logger import log_info


def configure_gpu(config):
    if not bpy.context.preferences.addons.get("cycles"):
        bpy.ops.preferences.addon_enable(module="cycles")

    bpy.context.scene.render.engine = "CYCLES"
    bpy.context.scene.cycles.device = "GPU"
    bpy.context.preferences.addons["cycles"].preferences.compute_device_type = "CUDA"

    bpy.context.preferences.addons["cycles"].preferences.get_devices()
    for d in bpy.context.preferences.addons["cycles"].preferences.devices:
        if "nvidia" in d["name"].lower():
            d["use"] = 1
            log_info(f"Using GPU: {d['name']}")

    bpy.context.scene.cycles.use_adaptive_sampling = config["render"]["adaptive_sampling"]


# render settings will be sent in as a dict from yaml
def main(config, num_frames):
    # configure the resolution before quitting in the case of
    # preview render mode to properly preview mobile/desktop viewports
    if config["render"]["is_mobile"]:
        log_info("Setting to mobile resolution...")
        bpy.context.scene.render.resolution_x = 1080
        bpy.context.scene.render.resolution_y = 1920

        bpy.context.scene.cycles.tile_x = 1080
        bpy.context.scene.cycles.tile_y = 1920
    elif config["render"]["is_4k"]:
        log_info("Setting to 4k desktop resolution...")
        bpy.context.scene.render.resolution_x = 3840
        bpy.context.scene.render.resolution_y = 2160

        # it is better to use 1 tile because gpu has 12GB of memory
        bpy.context.scene.cycles.tile_x = 3840
        bpy.context.scene.cycles.tile_y = 2160
    else:
        log_info("Setting to 1080p desktop resolution...")
        bpy.context.scene.render.resolution_x = 1920
        bpy.context.scene.render.resolution_y = 1080

        bpy.context.scene.cycles.tile_x = 1920
        bpy.context.scene.cycles.tile_y = 1080

    bpy.context.scene.render.fps = config["render"]["fps"]

    if config["pipeline"]["quick_validate_mode"]:
        bpy.context.scene.frame_end = 100
    else:
        bpy.context.scene.frame_end = num_frames

    # disbale relationship lines
    bpy.context.window_manager.windows.update()
    screen = bpy.context.window.screen

    for area in screen.areas:
        if area.type == 'VIEW_3D':
            for space in area.spaces:
                if space.type == 'VIEW_3D':
                    space.overlay.show_relationship_lines = False

    if config["pipeline"]["preview_mode"]:
        log_info("Set to preview mode, skipping rendering...")
        return

    log_info(f"Starting Rendering of {num_frames}")
    configure_gpu(config)

    bpy.context.scene.cycles.samples = config["render"]["samples"]
    bpy.context.scene.cycles.use_denoising = False

    # we want to render as a sequence of pngs so that we can add a background in vse
    bpy.context.scene.render.film_transparent = True
    # Set output format to PNG with RGBA channels
    bpy.context.scene.render.image_settings.file_format = "PNG"
    bpy.context.scene.render.image_settings.color_mode = "RGBA"

    frames_dir = get_frames_dir()
    os.system(f"rm -rf {frames_dir}")
    os.system(f"mkdir {frames_dir}")
    bpy.context.scene.render.filepath = f"{frames_dir}/frame_"

    bpy.ops.render.render(animation=True)

    log_info("Exiting render.py")
    bpy.ops.wm.quit_blender()
