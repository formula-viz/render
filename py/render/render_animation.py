import bpy
from utils.config import Config
from utils.project_structure import get_frames_dir


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
            print(f"Using GPU: {d['name']}")

    bpy.context.scene.cycles.use_adaptive_sampling = config.adaptive_sampling


# render settings will be sent in as a dict from yaml
def main(config: Config, num_frames):
    if not config.should_render:
        print("Set to not render, skipping rendering...")
        return

    print(f"Starting Rendering of {num_frames}")
    configure_gpu(config)

    if config.validate_render:
        bpy.context.scene.frame_end = 100
    else:
        bpy.context.scene.frame_end = num_frames

    bpy.context.scene.render.fps = config.fps
    bpy.context.scene.cycles.samples = config.samples
    bpy.context.scene.cycles.use_denoising = False

    if config.is_4k:
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
    frames_dir = get_frames_dir()
    bpy.context.scene.render.filepath = f"{frames_dir}/frame_"

    bpy.ops.render.render(animation=True)
