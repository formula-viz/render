import bpy
from mathutils import Vector

from py.render.render_funcs.add_start_finish_line import add_start_finish_line
from py.render.render_funcs.add_track import create_material, create_planes
from py.render.render_funcs.load_track_data import TrackData
from py.utils.colors import hex_to_blender_rgb
from py.utils.logger import log_info


class StatusTrack:
    def __init__(
        self, track_data, camera_obj, start_finish_line_idx, driver_df, is_shorts_output
    ):
        self.track_data = track_data
        self.camera_obj = camera_obj
        self.start_finish_line_idx = start_finish_line_idx
        self.driver_df = driver_df
        self.is_shorts_output = is_shorts_output

        log_info("Initializing StatusTrack...")

        # Create empty parent object for camera-relative positioning
        bpy.ops.object.empty_add(type="PLAIN_AXES", location=(0, 0, 0))
        self.parent_empty = bpy.context.active_object
        # ensure the parent empty is not rendered and invisible in viewport
        self.parent_empty.hide_render = True
        self.parent_empty.hide_viewport = True
        self.parent_empty.name = "StatusTrackParent"

        self._parent_to_camera(camera_obj)

        self._setup()

    def _setup(self):
        new_track_data, new_driver_df = self._center(
            self.track_data, self.driver_df)

        optimal_scale = self._calculate_optimal_scale(
            new_track_data, self.camera_obj, self.is_shorts_output
        )

        track_mat = create_material(hex_to_blender_rgb("#FFFFFF"), "Main")
        status_track_obj = create_planes(
            new_track_data.inner_curb_points,
            new_track_data.outer_curb_points,
            "Status",
            track_mat,
        )
        status_start_finish_line = add_start_finish_line(
            new_track_data.inner_points,
            new_track_data.outer_points,
            self.start_finish_line_idx,
            "StatusStartFinishLine",
            line_width=20,
        )

        self._scale(optimal_scale, status_track_obj)
        indicator_dot = self._add_indicator_dot(new_driver_df)

        # Parent both objects to the status track, for relative movement, this also scales them accordingly
        status_start_finish_line.parent = status_track_obj
        indicator_dot.parent = status_track_obj
        # finally, parent the status track to the parent empty
        status_track_obj.parent = self.parent_empty

    # TODO: this will need to be updated for different resolutions,
    # for now it just assumes it is in the phone mode
    def _parent_to_camera(self, camera_obj: bpy.types.Object) -> None:
        """Parent the leaderboard to the camera."""
        self.parent_empty.parent = camera_obj

        if self.is_shorts_output:
            position = (0.13, 0.31, -1)
        else:
            position = (0.28, 0.15, -1)

        self.parent_empty.location = Vector(position)
        self.parent_empty.rotation_euler = camera_obj.rotation_euler

    # TODO: this may need to be reworked later
    def _calculate_optimal_scale(self, new_track_data, camera_obj, is_shorts_output):
        # TODO: for now setting is_shorts_output to always True
        is_shorts_output = True

        # At 1 meter distance with 50mm lens
        TOTAL_WIDTH_COVERED = 0.72  # meters
        TOTAL_HEIGHT_COVERED = 0.48  # meters

        # Calculate usable space based on resolution aspect ratio
        if is_shorts_output:
            resolution_aspect = 1080 / 1920  # 0.5625 (9:16)
            usable_width = TOTAL_HEIGHT_COVERED * resolution_aspect
            usable_height = TOTAL_HEIGHT_COVERED
        else:
            resolution_aspect = 1920 / 1080  # 1.7778 (16:9)
            usable_height = TOTAL_WIDTH_COVERED / resolution_aspect
            usable_width = TOTAL_WIDTH_COVERED

        # Get track dimensions
        x_points = [point[0] for point in new_track_data.outer_points]
        y_points = [point[1] for point in new_track_data.outer_points]
        track_width = max(x_points) - min(x_points)
        track_height = max(y_points) - min(y_points)

        # Calculate desired size as fraction of usable space
        if is_shorts_output:
            desired_width = 0.45  # 40% of width
            desired_height = 0.3  # 20% of height
        else:
            desired_width = 0.3  # 30% of width
            desired_height = 0.25  # 25% of height

        desired_width_meters = usable_width * desired_width
        desired_height_meters = usable_height * desired_height

        scale_x = desired_width_meters / track_width
        scale_y = desired_height_meters / track_height

        return min(scale_x, scale_y)

    def _scale(self, optimal_scale, status_track_obj):
        status_track_obj.scale.x = optimal_scale
        status_track_obj.scale.y = optimal_scale
        status_track_obj.scale.z = optimal_scale

    def _center(self, new_track_data, new_driver_df):
        new_inner_points = []
        new_outer_points = []
        new_inner_curb_points = []
        new_outer_curb_points = []

        # offset will be based on the outer points
        min_x = min([point[0] for point in new_track_data.outer_points])
        max_x = max([point[0] for point in new_track_data.outer_points])
        offset_x = -(max_x + min_x) / 2

        min_y = min([point[1] for point in new_track_data.outer_points])
        max_y = max([point[1] for point in new_track_data.outer_points])
        offset_y = -(max_y + min_y) / 2

        min_z = min([point[2] for point in new_track_data.outer_points])
        max_z = max([point[2] for point in new_track_data.outer_points])
        offset_z = -(max_z + min_z) / 2

        offset = (offset_x, offset_y, offset_z)

        new_inner_points = [
            (x + offset[0], y + offset[1], z + offset[2])
            for x, y, z in new_track_data.inner_points
        ]
        new_outer_points = [
            (x + offset[0], y + offset[1], z + offset[2])
            for x, y, z in new_track_data.outer_points
        ]
        new_inner_curb_points = [
            (x + offset[0], y + offset[1], z + offset[2])
            for x, y, z in new_track_data.inner_curb_points
        ]
        new_outer_curb_points = [
            (x + offset[0], y + offset[1], z + offset[2])
            for x, y, z in new_track_data.outer_curb_points
        ]

        new_driver_df = new_driver_df.copy()
        new_driver_df["X"] = new_driver_df["X"] + offset_x
        new_driver_df["Y"] = new_driver_df["Y"] + offset_y
        new_driver_df["Z"] = new_driver_df["Z"] + offset_z

        new_track_data = TrackData(
            new_inner_points,
            new_outer_points,
            new_inner_curb_points,
            new_outer_curb_points,
        )

        return new_track_data, new_driver_df

    def _add_indicator_dot(self, new_driver_df):
        dot = self._create_indicator_dot()

        for i in range(len(new_driver_df)):
            frame = i + 1

            dot.location = (
                new_driver_df["X"].iloc[i], new_driver_df["Y"].iloc[i], 0)
            dot.keyframe_insert(data_path="location", frame=frame)

        return dot

    def _create_indicator_dot(self):
        bpy.ops.mesh.primitive_uv_sphere_add(
            radius=17, segments=64, ring_count=64)
        dot = bpy.context.active_object

        # Create material with emission
        dot_mat = bpy.data.materials.new(name="IndicatorDot")
        dot_mat.use_nodes = True
        nodes = dot_mat.node_tree.nodes
        nodes.clear()

        # Create emission node
        node_emission = nodes.new("ShaderNodeEmission")
        node_output = nodes.new("ShaderNodeOutputMaterial")

        # Set emission color and strength
        node_emission.inputs['Color'].default_value = (
            *hex_to_blender_rgb("#00FFFF"), 1)
        node_emission.inputs['Strength'].default_value = 2.0

        # Link nodes
        links = dot_mat.node_tree.links
        links.new(node_emission.outputs[0], node_output.inputs[0])

        dot.data.materials.append(dot_mat)

        return dot
