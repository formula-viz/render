import bpy
from mathutils import Vector

from utils.logger import log_info
from utils.project_structure import Resources


class RaceTimer:
    def __init__(self, config, camera_obj):
        """Adds a timer to the bottom right, showing the time elapsed since the start."""
        self.config = config
        self.camera_obj = camera_obj

        log_info("Initializing RaceTimer...")

        self.start_frame = config["render"]["start_buffer_frames"]

        self._create_timer()
        self._update_timer_text()

        self._parent_to_camera(self.camera_obj, self.timer_obj)

    def _create_timer(self):
        """Creates a text object to display the race timer."""
        # Create text object
        timer_curve = bpy.data.curves.new(name="Timer", type="FONT")
        self.timer_obj = bpy.data.objects.new(
            name="Timer", object_data=timer_curve)
        bpy.context.scene.collection.objects.link(self.timer_obj)

        self.timer_obj.data.body = "0:00.000"

        self.timer_obj.data.align_x = "LEFT"
        self.timer_obj.data.align_y = "CENTER"

        self.timer_obj.data.font = bpy.data.fonts.load(
            Resources.get_main_font())
        self.timer_obj.data.size = 0.03

        # Create white material
        mat = bpy.data.materials.new(name="TimerMaterial")
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        nodes["Principled BSDF"].inputs["Base Color"].default_value = (
            1,
            1,
            1,
            1,
        )  # Pure white RGBA

        # Assign material to text
        self.timer_obj.data.materials.append(mat)

    def _update_timer_text(self) -> None:
        """Updates timer text based on current frame using frame handler."""

        def update_frame(scene):
            frame = scene.frame_current
            if frame <= self.start_frame:
                self.timer_obj.data.body = "0:00.000"
                return

            elapsed_frames = frame - self.start_frame
            elapsed_time = elapsed_frames / self.config["render"]["fps"]

            minutes = int(elapsed_time // 60)
            seconds = int(elapsed_time % 60)
            milliseconds = int((elapsed_time % 1) * 1000)

            self.timer_obj.data.body = f"{minutes}:{
                seconds:02d}.{milliseconds:03d}"

        # Register and unregister handlers
        if update_frame not in bpy.app.handlers.frame_change_post:
            bpy.app.handlers.frame_change_post.append(update_frame)

    # TODO: this will need to be updated for different resolutions,
    # for now it just assumes it is in the phone mode
    def _parent_to_camera(self, camera_obj: bpy.types.Object, timer_obj) -> None:
        """Parent the leaderboard to the camera."""
        timer_obj.parent = camera_obj

        if self.config["render"]["is_shorts_output"]:
            position = (0.06, -0.33, -1)
        else:
            position = (0.22, -0.18, -1)

        timer_obj.location = Vector(position)
        timer_obj.rotation_euler = camera_obj.rotation_euler
