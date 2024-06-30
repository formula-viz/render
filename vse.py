import bpy

# Create a new scene
scene = bpy.context.scene

# Clear existing sequences
scene.sequence_editor_clear()

if not scene.sequence_editor:
    scene.sequence_editor_create()
scene.sequence_editor_clear()

# Load the video file
video_path = "~/Projects/formula-viz/render/tmp.mp4"
video_strip = scene.sequence_editor.sequences.new_movie(name="Video", filepath=video_path, channel=1, frame_start=1)

# Add a text strip
text = "Sample Text"
text_strip = scene.sequence_editor.sequences.new_effect(
    name="Text", type="TEXT", channel=2, frame_start=1, frame_end=video_strip.frame_final_duration
)

# Set text strip properties
text_strip.text = text
text_strip.location = (0.05, 0.95)  # Top left corner (normalized coordinates)
text_strip.font_size = 50
text_strip.use_shadow = True

# Set render settings
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.render.filepath = "output.mp4"
scene.render.image_settings.file_format = "FFMPEG"
scene.render.ffmpeg.format = "MPEG4"
scene.render.ffmpeg.codec = "H264"
scene.render.ffmpeg.constant_rate_factor = "HIGH"
scene.render.ffmpeg.ffmpeg_preset = "GOOD"
scene.render.ffmpeg.video_bitrate = 6000

# Render the video
bpy.ops.render.render(animation=True)
