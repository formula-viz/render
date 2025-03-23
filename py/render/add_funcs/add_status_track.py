"""A class for creating and managing a status track visualization in Blender.

The status track is a miniature representation of the track that displays
the current position of a driver as a dot. It is positioned relative to the camera
and scales appropriately based on the output mode (shorts or landscape).
"""

import math
from typing import Tuple

import bpy
from mathutils import Vector
from pandas import DataFrame

from py.render.add_funcs.add_flag import add_flag
from py.render.add_funcs.add_start_finish_line import add_start_finish_line
from py.render.add_funcs.add_track import create_material, create_planes
from py.render.data_funcs.load_track_data import TrackData
from py.utils.colors import hex_to_blender_rgb
from py.utils.config import Config
from py.utils.logger import log_info
from py.utils.project_structure import RESOURCES_DIR

# In the shorts mode, if we have a dot object, 1 meter away from the camera,
# an x value of 0.2 will be the edge and a y value of 0.36 will be the top edge
# This can be used to dynamically position the status track regardless of the
# particular dimensions of that particular track
SHORTS_MODE_RIGHT_EDGE = 0.2
SHORTS_MODE_TOP_EDGE = 0.36

# I guess they are symmetrical because of the aspect ratios, but this is not by design
LANDSCAPE_MODE_RIGHT_EDGE = 0.36
LANDSCAPE_MODE_TOP_EDGE = 0.2

LANDSCAPE_EDGE_BUFFER = 0.01
SHORTS_MODE_EDGE_BUFFER = 0.05


class StatusTrack:
    """A class for creating and managing a status track visualization in Blender.

    The status track is a miniature representation of the track that displays
    the current position of a driver as a dot. It is positioned relative to the camera
    and scales appropriately based on the output mode (shorts or landscape).
    """

    def __init__(
        self,
        track_data: TrackData,
        camera_obj: bpy.types.Object,
        start_finish_line_idx: int,
        driver_df: DataFrame,
        is_shorts_output: bool,
        config: Config,
    ):
        """Initialize the StatusTrack with track data and positioning parameters.

        Args:
            track_data: The track data containing inner and outer track points
            camera_obj: The camera object to parent the status track to
            start_finish_line_idx: Index of the start/finish line point
            driver_df: DataFrame containing driver position data over time
            is_shorts_output: Boolean indicating if output is for shorts format (vertical)
            config: Global configuration settings

        """
        self.track_data = track_data
        self.camera_obj = camera_obj
        self.start_finish_line_idx = start_finish_line_idx
        self.driver_df = driver_df
        self.is_shorts_output = is_shorts_output
        self.config = config

        self._create_parent_empty()
        log_info("Initializing StatusTrack...")

        scaled_track_width, scaled_track_height = self._setup()
        self._parent_to_camera(camera_obj, scaled_track_width, scaled_track_height)

    def _create_parent_empty(self):
        # Create empty parent object for camera-relative positioning
        bpy.ops.object.empty_add(type="PLAIN_AXES", location=(0, 0, 0))  # pyright: ignore
        active_obj = bpy.context.active_object
        if not active_obj:
            raise ValueError(
                "Failed to create parent empty: Active object is not a valid Blender Object"
            )

        # Explicitly cast to the correct type to make pyright happy
        self.parent_empty = active_obj

        # ensure the parent empty is not rendered and invisible in viewport
        self.parent_empty.hide_render = True
        self.parent_empty.hide_viewport = True
        self.parent_empty.name = "StatusTrackParent"

    def _widen_track(
        self, new_track_data: TrackData, total_widen: int
    ) -> tuple[list[tuple[float, float, float]], list[tuple[float, float, float]]]:
        """Widen track by moving inner and outer points 5 meters each outward.

        Args:
            new_track_data: Track data containing points to widen
            total_widen: Total amount to widen the track by

        Returns:
            TrackData with widened track points

        """
        new_inner_points: list[tuple[float, float, float]] = []
        new_outer_points: list[tuple[float, float, float]] = []

        for inner_point, outer_point in zip(
            new_track_data.inner_curb_points, new_track_data.outer_curb_points
        ):
            # Calculate vector from inner to outer point
            vector_x = outer_point[0] - inner_point[0]
            vector_y = outer_point[1] - inner_point[1]
            vector_z = outer_point[2] - inner_point[2]

            # Calculate vector length
            length = (vector_x**2 + vector_y**2 + vector_z**2) ** 0.5

            norm_x = vector_x / length
            norm_y = vector_y / length
            norm_z = vector_z / length

            # Widen by 5 meters in each direction
            widen_distance = total_widen / 2

            # Move inner point further inward
            new_inner_x = inner_point[0] - widen_distance * norm_x
            new_inner_y = inner_point[1] - widen_distance * norm_y
            new_inner_z = inner_point[2] - widen_distance * norm_z
            new_inner_points.append((new_inner_x, new_inner_y, new_inner_z))

            # Move outer point further outward
            new_outer_x = outer_point[0] + widen_distance * norm_x
            new_outer_y = outer_point[1] + widen_distance * norm_y
            new_outer_z = outer_point[2] + widen_distance * norm_z
            new_outer_points.append((new_outer_x, new_outer_y, new_outer_z))

        return new_inner_points, new_outer_points

    def _add_background(self, new_inner_points, new_outer_points):
        def calculate_background_points(
            base_points, reference_points, expansion=45, stride=5
        ):
            """Calculate background points from base and reference points.

            Args:
                base_points: Points to expand from (e.g., outer_curb_points)
                reference_points: Points used for direction calculation (e.g., outer_points)
                expansion: Distance to expand in units
                stride: Take every nth point

            Returns:
                List of calculated background points and total distance

            """
            result_points = []
            total_distance = 0

            for i in range(0, len(base_points), stride):
                base_point = base_points[i]
                ref_point = reference_points[i]

                vec = (
                    base_point[0] - ref_point[0],
                    base_point[1] - ref_point[1],
                    base_point[2] - ref_point[2],
                )
                length = (vec[0] ** 2 + vec[1] ** 2 + vec[2] ** 2) ** 0.5
                total_distance += length

                if length > 0:
                    normalized = (vec[0] / length, vec[1] / length, vec[2] / length)
                else:
                    normalized = (0, 0, 0)

                new_point = (
                    base_point[0] - expansion * normalized[0],
                    base_point[1] - expansion * normalized[1],
                    base_point[2],  # Keep Z the same
                )
                result_points.append(new_point)

            return result_points, total_distance

        # Calculate outer and inner background points, using every 5th point
        outer_bg_points, outer_total_distance = calculate_background_points(
            new_outer_points, new_inner_points, stride=15
        )

        inner_bg_points, inner_total_distance = calculate_background_points(
            new_inner_points, new_outer_points, stride=15
        )

        # Choose the points with the longer distance
        if outer_total_distance >= inner_total_distance:
            status_track_background_points = outer_bg_points
        else:
            status_track_background_points = inner_bg_points

        # Create a mesh for the background
        bg_mesh = bpy.data.meshes.new("StatusTrackBackgroundMesh")
        bg_obj = bpy.data.objects.new("StatusTrackBackground", bg_mesh)
        bpy.context.scene.collection.objects.link(bg_obj)

        # Create vertices and faces for the mesh
        vertices = [(p[0], p[1], p[2]) for p in status_track_background_points]

        # Create a single face that includes all vertices
        faces = [list(range(len(vertices)))]

        # Update the mesh with the vertices and faces
        bg_mesh.from_pydata(vertices, [], faces)
        bg_mesh.update()

        # Create material for the background with transparency
        bg_mat = bpy.data.materials.new(name="StatusTrackBackgroundMaterial")
        bg_mat.use_nodes = True

        # Clear default nodes
        if bg_mat.node_tree:
            bg_mat.node_tree.nodes.clear()

        # Add nodes for transparent material
        node_tree = bg_mat.node_tree
        output = node_tree.nodes.new(type="ShaderNodeOutputMaterial")
        principled = node_tree.nodes.new(type="ShaderNodeBsdfPrincipled")

        # Set up semi-transparent material
        dark_gray = hex_to_blender_rgb("#222223")
        principled.inputs["Base Color"].default_value = (
            dark_gray[0],
            dark_gray[1],
            dark_gray[2],
            1.0,
        )
        principled.inputs["Alpha"].default_value = 0.2

        # Connect nodes
        node_tree.links.new(principled.outputs["BSDF"], output.inputs["Surface"])

        # Enable transparency
        bg_mat.blend_method = "BLEND"
        bg_obj.data.materials.append(bg_mat)

        # Position the background slightly behind the track to avoid z-fighting
        bg_obj.location.z = -0.001

        # Parent the background to the status track object
        return bg_obj

    def _get_spread(self, points: list[tuple[float, float, float]], spread_val: float):
        # we want to create an inner and outer spread, essentially
        spread_a = []
        spread_b = []
        for i in range(len(points)):
            # find vec between cur and prev
            next = points[i + 1] if i < len(points) - 1 else points[0]
            cur = points[i]
            vec = (next[0] - cur[0], next[1] - cur[1])

            # find the perpendicular
            perp = (-vec[1], vec[0])
            length = math.sqrt(perp[0] ** 2 + perp[1] ** 2)
            perp_norm = (perp[0] / length, perp[1] / length, 0)

            spread_a.append(
                (
                    cur[0] + perp_norm[0] * spread_val,
                    cur[1] + perp_norm[1] * spread_val,
                    0,
                )
            )
            spread_b.append(
                (
                    cur[0] - perp_norm[0] * spread_val,
                    cur[1] - perp_norm[1] * spread_val,
                    0,
                )
            )
        return spread_a, spread_b

    def _add_start_finish_line(self, a_points, b_points) -> bpy.types.Object:
        for i in range(len(a_points)):
            a_points[i] = (a_points[i][0], a_points[i][1], 1)
            b_points[i] = (b_points[i][0], b_points[i][1], 1)

        status_start_finish_line = add_start_finish_line(
            a_points,
            b_points,
            self.start_finish_line_idx,
            "StatusStartFinishLine",
            line_width=40,
        )
        # Create start/finish line material with texture
        start_finish_mat = bpy.data.materials.new(name="StartFinishLineMaterial")
        start_finish_mat.use_nodes = True
        if start_finish_mat.node_tree:
            nodes = start_finish_mat.node_tree.nodes
            links = start_finish_mat.node_tree.links

            # Clear default nodes
            nodes.clear()

            # Add texture image node
            texture_node = nodes.new(type="ShaderNodeTexImage")
            texture_path = bpy.path.abspath(
                f"{RESOURCES_DIR}/start-finish-line-texture.png"
            )
            texture_image = bpy.data.images.load(texture_path)
            texture_node.image = texture_image

            # Add UV mapping nodes for proper texture projection
            mapping_node = nodes.new(type="ShaderNodeMapping")
            texcoord_node = nodes.new(type="ShaderNodeTexCoord")

            # Add principled BSDF node
            bsdf_node = nodes.new(type="ShaderNodeBsdfPrincipled")
            output_node = nodes.new(type="ShaderNodeOutputMaterial")

            # Connect nodes for proper UV mapping
            links.new(texcoord_node.outputs["UV"], mapping_node.inputs["Vector"])
            links.new(mapping_node.outputs["Vector"], texture_node.inputs["Vector"])
            links.new(texture_node.outputs["Color"], bsdf_node.inputs["Base Color"])
            links.new(bsdf_node.outputs["BSDF"], output_node.inputs["Surface"])

        # Apply material to start/finish line
        status_start_finish_line.data.materials[0] = start_finish_mat  # pyright: ignore

        # Ensure proper UV mapping
        # Select the object and enter edit mode
        bpy.context.view_layer.objects.active = status_start_finish_line
        bpy.ops.object.mode_set(mode="EDIT")

        # Select all faces and perform unwrap
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.uv.unwrap(method="ANGLE_BASED", margin=0.001)

        # Return to object mode
        bpy.ops.object.mode_set(mode="OBJECT")
        return status_start_finish_line

    def _setup(self) -> Tuple[float, float]:
        new_track_data, new_driver_df = self._center(self.track_data, self.driver_df)

        new_inner_points, new_outer_points = self._widen_track(new_track_data, 10)
        track_width, track_height = self._get_track_dimensions(
            new_inner_points, new_outer_points
        )
        optimal_scale = self._calculate_optimal_scale(
            track_width, track_height, self.camera_obj, self.is_shorts_output
        )
        scaled_track_width, scaled_track_height = (
            track_width * optimal_scale,
            track_height * optimal_scale,
        )

        spread_val = 6
        inner_spread_a, inner_spread_b = self._get_spread(new_inner_points, spread_val)
        outer_spread_a, outer_spread_b = self._get_spread(new_outer_points, spread_val)

        track_mat = create_material(hex_to_blender_rgb("#FFFFFF"), "Main")
        inner_spread_obj = create_planes(
            inner_spread_a,
            inner_spread_b,
            "InnerStatusSpread",
            track_mat,
        )

        outer_spread_obj = create_planes(
            outer_spread_a,
            outer_spread_b,
            "OuterStatusSpread",
            track_mat,
        )

        # given outer_spread_a, outer_spread_b, and inner, we want to find the sets which are furthest
        # so either, outer_spread_a and inner a or b
        # or outer_spread_b and inner a or b
        def dist(a, b):
            return math.sqrt(
                (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2
            )

        max_dist = 0
        cur_as = []
        cur_bs = []
        if dist(outer_spread_a[0], inner_spread_a[0]) > max_dist:
            max_dist = dist(outer_spread_a[0], outer_spread_b[0])
            cur_as = outer_spread_a
            cur_bs = outer_spread_b
        if dist(outer_spread_a[0], inner_spread_b[0]) > max_dist:
            max_dist = dist(outer_spread_a[0], inner_spread_b[0])
            cur_as = outer_spread_a
            cur_bs = inner_spread_b
        if dist(outer_spread_b[0], inner_spread_a[0]) > max_dist:
            max_dist = dist(outer_spread_b[0], inner_spread_a[0])
            cur_as = outer_spread_b
            cur_bs = inner_spread_a
        if dist(outer_spread_b[0], inner_spread_b[0]) > max_dist:
            max_dist = dist(outer_spread_b[0], inner_spread_b[0])
            cur_as = outer_spread_b
            cur_bs = inner_spread_b

        status_start_finish_line = self._add_start_finish_line(cur_as, cur_bs)

        background_obj = self._add_background(new_inner_points, new_outer_points)

        self._scale(optimal_scale, inner_spread_obj)
        self._scale(optimal_scale, outer_spread_obj)
        self._scale(optimal_scale, status_start_finish_line)
        self._scale(optimal_scale, background_obj)

        indicator_dot = self._add_indicator_dot(new_driver_df)
        indicator_dot.parent = inner_spread_obj

        status_start_finish_line.parent = self.parent_empty
        inner_spread_obj.parent = self.parent_empty
        outer_spread_obj.parent = self.parent_empty
        background_obj.parent = self.parent_empty

        return scaled_track_width, scaled_track_height

    # TODO: this will need to be updated for different resolutions,
    # for now it just assumes it is in the phone mode
    def _parent_to_camera(
        self,
        camera_obj: bpy.types.Object,
        scaled_track_width: float,
        scaled_track_height: float,
    ) -> None:
        """Parent the leaderboard to the camera."""
        if not self.parent_empty:
            raise ValueError("Parent empty has not been initialized")

        self.parent_empty.parent = camera_obj

        # the track will already be centered so its highest point will be scaled_track_height / 2
        up_y, right_x = scaled_track_height / 2, scaled_track_width / 2

        if self.is_shorts_output:
            position = (
                SHORTS_MODE_RIGHT_EDGE - right_x - SHORTS_MODE_EDGE_BUFFER,
                SHORTS_MODE_TOP_EDGE - up_y - SHORTS_MODE_EDGE_BUFFER,
                -1,
            )
        else:
            position = (
                LANDSCAPE_MODE_RIGHT_EDGE - right_x - LANDSCAPE_EDGE_BUFFER,
                LANDSCAPE_MODE_TOP_EDGE - up_y - LANDSCAPE_EDGE_BUFFER,
                -1,
            )

        self.parent_empty.location = Vector(position)
        self.parent_empty.rotation_euler = camera_obj.rotation_euler

    def _get_track_dimensions(
        self, new_inner_points, new_outer_points
    ) -> Tuple[float, float]:
        """Calculate the width and height of the track."""
        # Get track dimensions for inner points
        inner_x_points = [point[0] for point in new_inner_points]
        inner_y_points = [point[1] for point in new_inner_points]
        inner_track_width = max(inner_x_points) - min(inner_x_points)
        inner_track_height = max(inner_y_points) - min(inner_y_points)

        # Get track dimensions for outer points
        outer_x_points = [point[0] for point in new_outer_points]
        outer_y_points = [point[1] for point in new_outer_points]
        outer_track_width = max(outer_x_points) - min(outer_x_points)
        outer_track_height = max(outer_y_points) - min(outer_y_points)

        # Use the maximum of inner and outer dimensions
        track_width = max(inner_track_width, outer_track_width)
        track_height = max(inner_track_height, outer_track_height)

        return track_width, track_height

    # TODO: this may need to be reworked later
    def _calculate_optimal_scale(
        self,
        track_width: float,
        track_height: float,
        camera_obj: bpy.types.Object,
        is_shorts_output: bool,
    ) -> float:
        # At 1 meter distance with 50mm lens
        total_width_covered = 0.72  # meters
        total_height_covered = 0.48  # meters

        # Calculate usable space based on resolution aspect ratio
        if is_shorts_output:
            resolution_aspect = 1080 / 1920  # 0.5625 (9:16)
            usable_width = total_height_covered * resolution_aspect
            usable_height = total_height_covered
        else:
            resolution_aspect = 1920 / 1080  # 1.7778 (16:9)
            usable_height = total_width_covered / resolution_aspect
            usable_width = total_width_covered

        # Calculate desired size as fraction of usable space
        if is_shorts_output:
            desired_width = 0.30
            desired_height = 0.25
        else:
            desired_width = 0.20
            desired_height = 0.25

        desired_width_meters = usable_width * desired_width
        desired_height_meters = usable_height * desired_height

        scale_x = desired_width_meters / track_width
        scale_y = desired_height_meters / track_height

        return min(scale_x, scale_y)

    def _scale(self, optimal_scale: float, status_track_obj: bpy.types.Object) -> None:
        status_track_obj.scale.x = optimal_scale
        status_track_obj.scale.y = optimal_scale
        status_track_obj.scale.z = optimal_scale

    def _center(
        self, new_track_data: TrackData, driver_df: DataFrame
    ) -> tuple[TrackData, DataFrame]:
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

        new_driver_df = driver_df.copy()
        new_driver_df["X"] = new_driver_df["X"] + offset_x
        new_driver_df["Y"] = new_driver_df["Y"] + offset_y
        new_driver_df["Z"] = new_driver_df["Z"] + offset_z

        new_track_data = TrackData(
            new_inner_points,
            None,
            new_outer_points,
            None,
            new_inner_curb_points,
            new_outer_curb_points,
        )

        return new_track_data, new_driver_df

    def _add_indicator_dot(self, new_driver_df: DataFrame) -> bpy.types.Object:
        indicator = add_flag(self.config, None, 150.0)
        is_flag = True
        if indicator is None:
            indicator = self._create_indicator_dot()
            is_flag = False

        x_vals = new_driver_df["X"].astype(float)
        y_vals = new_driver_df["Y"].astype(float)

        for i in range(len(x_vals)):
            frame = i + 1
            if is_flag:
                indicator.location = (x_vals[i], y_vals[i], 10)
            else:
                indicator.location = (x_vals[i], y_vals[i], 0)
            indicator.keyframe_insert(data_path="location", frame=frame)  # pyright: ignore

        return indicator

    def _create_indicator_dot(self) -> bpy.types.Object:
        bpy.ops.mesh.primitive_uv_sphere_add(radius=45, segments=64, ring_count=64)  # pyright: ignore
        dot = bpy.context.active_object
        if not dot:
            raise ValueError("Failed to create indicator dot")

        # Create material with emission
        dot_mat = bpy.data.materials.new(name="IndicatorDot")

        dot_mat.use_nodes = True
        node_tree = dot_mat.node_tree
        if not isinstance(node_tree, bpy.types.NodeTree):
            raise ValueError("Failed to get node tree")

        nodes = node_tree.nodes
        nodes.clear()  # pyright: ignore

        # Create emission node
        node_emission = nodes.new("ShaderNodeEmission")
        node_output = nodes.new("ShaderNodeOutputMaterial")

        # Set emission color and strength
        node_emission.inputs["Color"].default_value = (  # pyright: ignore
            *hex_to_blender_rgb("#00FFFF"),
            1,
        )
        node_emission.inputs["Strength"].default_value = 2.0  # pyright: ignore

        # Link nodes
        links = node_tree.links
        links.new(node_emission.outputs[0], node_output.inputs[0])

        dot.data.materials.append(dot_mat)  # pyright: ignore

        return dot
