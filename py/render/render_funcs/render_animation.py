"""Set up blender's render settings based on config.

Configures resolution, frame rate, and rendering settings based on the provided
configuration, then initiates either Cycles or Eevee rendering process.

Conditionally does not start the render process if in development settings ui_mode.
"""

import os

import bpy

from py.utils.config import Config
from py.utils.logger import log_info
from py.utils.project_structure import OUTPUT_DIR


def configure_output(config):
    """Configure ffmpeg mp4 output settings."""
    scene = bpy.context.scene
    if not scene:
        raise ValueError("Scene not found")

    output_path = os.path.join(OUTPUT_DIR, config["render"]["output"])
    scene.render.filepath = output_path

    scene.render.image_settings.file_format = "FFMPEG"
    scene.render.ffmpeg.format = "MPEG4"
    scene.render.ffmpeg.codec = "H264"
    scene.render.ffmpeg.constant_rate_factor = "PERC_LOSSLESS"


def eevee_render(config, num_frames, is_ui_mode):
    """Incorporate all possible settings for Eevee rendering."""
    log_info(f"Starting Eevee render of {num_frames} with preview_mode={is_ui_mode}...")

    scene = bpy.data.scenes["Scene"]
    scene.render.engine = "BLENDER_EEVEE"  # type: ignore

    eevee = scene.eevee
    if not eevee:
        raise ValueError("Eevee settings not found")

    # Sampling
    eevee.taa_render_samples = config["render"]["samples"]
    # only affects viewport
    eevee.taa_samples = config["render"]["samples"]

    # Ambient Occlusion
    # I don't see a visual impact of ambient occlusion, I'm leaving it out

    # Bloom, bright pixels produce a glowing effect, mimicking real cameras
    # This adds depth to the cars, I like it.
    eevee.use_bloom = True  # type: ignore
    # The defaults are sensible, but I like the bloom color as cyan
    eevee.bloom_color = (0.0, 1.0, 1.0)  # type: ignore

    # Depth of Field
    # I don't see a visual impact of depth of field, I'm not editing the defaults

    # Subsurface scattering is too technical to matter

    # Screen Space Reflections
    eevee.use_ssr = True  # type: ignore
    # this gets technical, I'm just going to enable and leave with the defaults

    # Motion Blur
    # I'm leaving it off, don't see a difference

    # Leaving Volumetrics Off, it seems to be for mist or fog

    # Not Touching Performance, Curves

    # Shadows, really affect the visuals. maxing this out
    eevee.shadow_cube_size = "4096"  # type: ignore
    eevee.shadow_cascade_size = "4096"  # type: ignore
    eevee.use_shadow_high_bitdepth = True  # type: ignore
    eevee.use_soft_shadows = True  # type: ignore

    # Not touching Indirect Lighting

    # Film, having a filter value over 1.0 really smooths the fine lines
    # Makes it look sharp, professional at the cost of a small level of detail
    scene.render.filter_size = 2.5

    # Simplify, I actually don't think this makes it look worse,
    # TODO: may be worth it to have this for quicker renders, especially
    # if I eventually transition to eevee

    # Not touching Grease Pencil or Freestyle

    # Color Management, this is very important for aesthetics
    scene.display_settings.display_device = "sRGB"  # type: ignore
    scene.view_settings.view_transform = "AgX"  # type: ignore
    scene.view_settings.look = "AgX - Base Contrast"  # type: ignore
    scene.view_settings.gamma = 0.95

    if not is_ui_mode:
        bpy.ops.render.render(animation=True)
        log_info("Render complete")
        bpy.ops.wm.quit_blender()


def cycles_render(config, num_frames, is_ui_mode):
    """TODO, needs proper config"""
    scene = bpy.context.scene
    if not scene:
        raise ValueError("Scene not found")

    scene.render.engine = "CYCLES"  # type: ignore

    scene.cycles.samples = config["render"]["samples"]
    scene.cycles.use_denoising = True

    if not is_ui_mode:
        log_info(f"Starting Cycles Render of {num_frames}")
        bpy.ops.render.render(animation=True)
        log_info("Cycles render complete")
        bpy.ops.wm.quit_blender()


def main(config: Config, num_frames: int):
    """Set up blender's render settings based on config.

    Configures resolution, frame rate, and rendering settings based on the provided
    configuration, then initiates either Cycles or Eevee rendering process.

    Conditionally does not start the render process if in development settings ui_mode.

    Args:
        config: Configuration object containing rendering and development settings
        num_frames: Total number of frames to render in the animation

    """
    scene = bpy.context.scene
    if not scene:
        raise ValueError("Scene not found")

    # configure the resolution before quitting in the case of
    # preview render mode to properly preview mobile/desktop viewports
    if config["render"]["is_shorts_output"]:
        log_info("Setting to shorts/phone resolution...")
        scene.render.resolution_x = 1080
        scene.render.resolution_y = 1920

        scene.cycles.tile_x = 1080
        scene.cycles.tile_y = 1920
    else:
        log_info("Setting to 4k desktop resolution...")
        scene.render.resolution_x = 3840
        scene.render.resolution_y = 2160

        # it is better to use 1 tile because gpu has 12GB+ of memory
        scene.cycles.tile_x = 3840
        scene.cycles.tile_y = 2160

    scene.render.fps = config["render"]["fps"]
    scene.frame_end = num_frames

    window = bpy.context.window
    if not window:
        raise ValueError("Window not found")

    screen = window.screen
    for area in screen.areas:
        if area.type == "VIEW_3D":
            for space in area.spaces:
                if space.type == "VIEW_3D":
                    space.overlay.show_relationship_lines = False  # type: ignore
                    space.overlay.show_outline_selected = False  # type: ignore
                    space.overlay.show_object_origins = False  # type: ignore

    if config["dev_settings"]["limited_frames_mode"]:
        scene.frame_end = 100

    configure_output(config)
    if config["render"]["engine"] == "cycles":
        cycles_render(config, num_frames, config["dev_settings"]["ui_mode"])
    else:
        eevee_render(config, num_frames, config["dev_settings"]["ui_mode"])
