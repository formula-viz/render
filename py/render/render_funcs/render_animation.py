from py.utils.colors import SCENE_BG_COLOR
import os

import bpy
from py.utils.project_structure import OUTPUT_DIR
from py.utils.logger import log_info


def configure_output(config):
    """Considers all output settings"""
    scene = bpy.context.scene

    # Set output path
    output_path = os.path.join(OUTPUT_DIR, config["render"]["output"])
    scene.render.filepath = output_path

    scene.render.image_settings.file_format = "FFMPEG"
    scene.render.ffmpeg.format = "MPEG4"
    scene.render.ffmpeg.codec = "H264"
    scene.render.ffmpeg.constant_rate_factor = "PERC_LOSSLESS"


def eevee_render(config, num_frames, is_preview_mode):
    """This incorporates all possible settings for Eevee rendering."""
    log_info(
        f"Starting Eevee render of {num_frames} with preview_mode={is_preview_mode}...")

    scene = bpy.data.scenes["Scene"]
    scene.render.engine = 'BLENDER_EEVEE'

    # Sampling
    scene.eevee.taa_render_samples = config["render"]["samples"]
    # only affects viewport
    scene.eevee.taa_samples = config["render"]["samples"]

    # Ambient Occlusion
    # I don't see a visual impact of ambient occlusion, I'm leaving it out

    # Bloom, bright pixels produce a glowing effect, mimicking real cameras
    # This adds depth to the cars, I like it.
    scene.eevee.use_bloom = True
    # The defaults are sensible, but I like the bloom color as cyan
    scene.eevee.bloom_color = (0.0, 1.0, 1.0)

    # Depth of Field
    # I don't see a visual impact of depth of field, I'm not editing the defaults

    # Subsurface scattering is too technical to matter

    # Screen Space Reflections
    scene.eevee.use_ssr = True
    # this gets technical, I'm just going to enable and leave with the defaults

    # Motion Blur
    # I'm leaving it off, don't see a difference

    # Leaving Volumetrics Off, it seems to be for mist or fog

    # Not Touching Performance, Curves

    # Shadows, really affect the visuals. maxing this out
    scene.eevee.shadow_cube_size = "4096"
    scene.eevee.shadow_cascade_size = "4096"
    scene.eevee.use_shadow_high_bitdepth = True
    scene.eevee.use_soft_shadows = True

    # Not touching Indirect Lighting

    # Film, having a filter value over 1.0 really smooths the fine lines
    # Makes it look sharp, professional at the cost of a small level of detail
    scene.render.filter_size = 2.5

    # Simplify, I actually don't think this makes it look worse,
    # TODO: may be worth it to have this for quicker renders, especially
    # if I eventually transition to eevee

    # Not touching Grease Pencil or Freestyle

    # Color Management, this is very important for aesthetics
    scene.display_settings.display_device = 'sRGB'
    scene.view_settings.view_transform = 'AgX'
    scene.view_settings.look = 'AgX - Base Contrast'
    scene.view_settings.gamma = 0.95

    if not is_preview_mode:
        bpy.ops.render.render(animation=True)
        log_info("Render complete")
        bpy.ops.wm.quit_blender()


def cycles_render(config, num_frames, is_preview_mode):
    """TODO, needs rework, got settings from GPT"""
    bpy.context.scene.render.engine = "CYCLES"

    bpy.context.scene.cycles.samples = config["render"]["samples"]
    bpy.context.scene.cycles.use_denoising = True

    if not is_preview_mode:
        log_info(f"Starting Cycles Render of {num_frames}")
        bpy.ops.render.render(animation=True)
        log_info("Cycles render complete")
        bpy.ops.wm.quit_blender()


# render settings will be sent in as a dict from yaml
def main(config, num_frames):
    # configure the resolution before quitting in the case of
    # preview render mode to properly preview mobile/desktop viewports
    if config["render"]["is_shorts_output"]:
        log_info("Setting to shorts/phone resolution...")
        bpy.context.scene.render.resolution_x = 1080
        bpy.context.scene.render.resolution_y = 1920

        bpy.context.scene.cycles.tile_x = 1080
        bpy.context.scene.cycles.tile_y = 1920
    else:
        log_info("Setting to 4k desktop resolution...")
        bpy.context.scene.render.resolution_x = 3840
        bpy.context.scene.render.resolution_y = 2160

        # it is better to use 1 tile because gpu has 12GB+ of memory
        bpy.context.scene.cycles.tile_x = 3840
        bpy.context.scene.cycles.tile_y = 2160
    bpy.context.view_layer.update()

    bpy.context.scene.render.fps = config["render"]["fps"]
    bpy.context.scene.frame_end = num_frames

    # disable relationship lines
    bpy.context.window_manager.windows.update()
    screen = bpy.context.window.screen
    for area in screen.areas:
        if area.type == "VIEW_3D":
            for space in area.spaces:
                if space.type == "VIEW_3D":
                    space.overlay.show_relationship_lines = False
                    space.overlay.show_outline_selected = False
                    space.overlay.show_object_origins = False

    if config["pipeline"]["quick_validate_mode"]:
        bpy.context.scene.frame_end = 100

    configure_output(config)
    if config["render"]["engine"] == "cycles":
        cycles_render(config, num_frames, config["pipeline"]["preview_mode"])
    else:
        eevee_render(config, num_frames, config["pipeline"]["preview_mode"])
