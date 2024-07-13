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
    bpy.context.scene.render.fps = render_settings["fps"]

    bpy.context.scene.cycles.samples = render_settings["samples"]

    bpy.context.scene.cycles.use_denoising = False

    resolution = render_settings["resolution"]
    bpy.context.scene.render.resolution_x = resolution["width"]
    bpy.context.scene.render.resolution_y = resolution["height"]

    bpy.context.scene.render.image_settings.file_format = "FFMPEG"
    bpy.context.scene.render.ffmpeg.format = "MPEG4"
    bpy.context.scene.render.ffmpeg.codec = "H264"
    bpy.context.scene.render.ffmpeg.constant_rate_factor = "HIGH"
    bpy.context.scene.render.filepath = "test.mp4"

    bpy.ops.render.render(animation=True)
