import os

import bpy
from py.utils.project_structure import OUTPUT_DIR
from py.utils.logger import log_info


def configure_output(config):
    # High quality video encoding with focus on sharpness
    bpy.context.scene.render.image_settings.file_format = "FFMPEG"
    bpy.context.scene.render.ffmpeg.format = "MPEG4"
    bpy.context.scene.render.ffmpeg.codec = "H264"
    # Use constant rate factor instead of bitrate control
    bpy.context.scene.render.ffmpeg.constant_rate_factor = "MEDIUM"
    bpy.context.scene.render.ffmpeg.ffmpeg_preset = "BEST"
    # Remove bitrate constraints that might cause quality issues
    bpy.context.scene.render.ffmpeg.video_bitrate = 0
    # Other quality settings
    bpy.context.scene.render.ffmpeg.gopsize = 1
    bpy.context.scene.render.ffmpeg.use_max_b_frames = False
    bpy.context.scene.render.ffmpeg.audio_codec = "NONE"
    bpy.context.scene.render.image_settings.color_mode = "RGB"
    bpy.context.scene.render.image_settings.compression = 0

    # Set output path
    output_path = os.path.join(OUTPUT_DIR, config["render"]["output"])
    bpy.context.scene.render.filepath = output_path


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

    bpy.context.scene.cycles.use_adaptive_sampling = True


def eevee_render(config, num_frames, is_preview_mode):
    log_info("Starting Eevee render...")

    # Set render engine to Eevee
    bpy.context.scene.render.engine = 'BLENDER_EEVEE'

    # Configure high quality Eevee settings
    eevee = bpy.context.scene.eevee
    eevee.taa_render_samples = config["render"]["samples"]
    eevee.taa_samples = config["render"]["samples"]
    eevee.use_taa_reprojection = True
    eevee.use_soft_shadows = True
    eevee.shadow_cube_size = "4096"  # Higher shadow resolution
    eevee.shadow_cascade_size = "4096"
    eevee.use_gtao = True  # Better ambient occlusion
    eevee.gtao_quality = 1.0
    eevee.use_ssr = True  # Screen space reflections
    eevee.ssr_quality = 1.0
    eevee.ssr_max_roughness = 1.0
    eevee.use_ssr_halfres = False
    eevee.use_bloom = True  # Add bloom effect
    eevee.bloom_threshold = 1.0
    eevee.bloom_knee = 0.5
    eevee.bloom_radius = 6.5
    eevee.bloom_intensity = 0.05

    if not is_preview_mode:
        # Perform proper render (not viewport)
        bpy.ops.render.render(animation=True)
        log_info("Render complete")
        bpy.ops.wm.quit_blender()


def cycles_render(config, num_frames, is_preview_mode):
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
