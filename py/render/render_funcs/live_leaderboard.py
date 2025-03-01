import bpy
from mathutils import Vector

from py.render.render_funcs.driver_circle import DriverCircle
from py.utils.logger import log_info
from py.utils.project_structure import Resources


class LiveLeaderboard:
    def __init__(
        self,
        config,
        driver_abbrevs: list[str],
        driver_colors: list[str],
        car_rankings: list[list[tuple[str, float]]],
        is_fancy_mode: bool,
        camera_obj: bpy.types.Object,
    ):
        """Create the live leaderboard.

        Args:
            driver_abbrevs: List of driver abbreviations (e.g., ['HAM', 'VER'])
            driver_colors: List of hex color codes for each driver

        """
        if not (len(driver_abbrevs) == len(driver_colors)):
            raise ValueError("All input lists must have the same length")

        log_info("Initializing LiveLeaderboard...")

        self.config = config
        self.driver_abbrevs = driver_abbrevs
        self.driver_colors = driver_colors
        self.car_rankings = car_rankings
        self.is_fancy_mode = is_fancy_mode
        self.driver_objects = {}  # Store references to driver objects
        self.camera_obj = camera_obj

        if self.is_fancy_mode:
            self.spacing = 0.035
        else:
            self.spacing = 0.015  # Vertical spacing between elements

        # Create main collection
        self.collection = bpy.data.collections.new("LiveLeaderboard")
        bpy.context.scene.collection.children.link(self.collection)

        # Create empty parent object for camera-relative positioning
        bpy.ops.object.empty_add(type="PLAIN_AXES", location=(0, 0, 0))
        self.parent_empty = bpy.context.active_object
        # ensure the parent empty is not rendered and invisible in viewport
        self.parent_empty.hide_render = True
        self.parent_empty.hide_viewport = True
        self.parent_empty.name = "LeaderboardParent"

        self._parent_to_camera()

        # Initialize
        self.position_offsets = self._get_offsets_dict()
        self._build_initial_objs()
        self._update_driver_positions()

    def _update_driver_positions(self) -> None:
        start_buffer_frames = self.config["render"]["start_buffer_frames"]

        for frame, ranking in enumerate(self.car_rankings):
            if frame % 10 != 0 and frame != len(self.car_rankings) - 1:
                continue

            true_frame = frame + start_buffer_frames

            new_order = [x[0] for x in ranking]

            for idx, driver in enumerate(new_order):
                empty_parent_obj = self.driver_objects[driver]

                empty_parent_obj.location = self.position_offsets[idx + 1]
                empty_parent_obj.keyframe_insert(data_path="location", frame=true_frame)

    def _parent_to_camera(self) -> None:
        """Parent the leaderboard to the camera."""
        self.parent_empty.parent = self.camera_obj

        if self.config["render"]["is_shorts_output"]:
            if self.is_fancy_mode:
                position = (-0.17, 0.32, -1)
            else:
                position = (-0.19, 0.32, -1)
        elif self.is_fancy_mode:
            position = (-0.33, 0.17, -1)
        else:
            position = (-0.35, 0.18, -1)

        self.parent_empty.location = Vector(position)
        self.parent_empty.rotation_euler = self.camera_obj.rotation_euler

    def _build_initial_objs(self) -> None:
        """Create initial objects for each driver in the leaderboard."""
        for idx, (abbrev, color) in enumerate(
            zip(self.driver_abbrevs, self.driver_colors)
        ):
            position = idx + 1
            empty_obj = self._create_element_obj(abbrev, color)

            empty_obj.location = self.position_offsets[position]

            self.driver_objects[abbrev] = empty_obj

    def _create_element_obj(self, abbrev: str, color: str) -> bpy.types.Object:
        """Create an empty object as parent for the driver's text object.

        Args:
            abbrev: Driver abbreviation
            color: Hex color code for the driver

        Returns:
            bpy.types.Object: Empty object that parents the driver's text

        """
        # Create empty parent for text
        bpy.ops.object.empty_add(type="PLAIN_AXES", location=(0, 0, 0))
        empty_obj = bpy.context.active_object
        empty_obj.name = f"Empty_{abbrev}"
        empty_obj.hide_render = True
        empty_obj.hide_viewport = True
        empty_obj.parent = self.parent_empty

        # Create driver circle if in fancy mode
        if self.is_fancy_mode:
            self.driver_circle = DriverCircle(
                driver_abbrev=abbrev,
                color=color,
                driver_car_obj=None,  # Using empty_obj as the parent
                camera_obj=None,
                pre_existing_empty=empty_obj,
            )
            self.driver_circle.circle_face.scale = (0.015, 0.015, 0.015)

        # Create text object
        if self.is_fancy_mode:
            text_loc = (0.02, -0.005, 0)
        else:
            text_loc = (0, 0, 0)

        bpy.ops.object.text_add(location=text_loc)
        text_obj = bpy.context.active_object
        text_obj.name = f"Text_{abbrev}"
        text_obj.data.body = abbrev
        text_obj.parent = empty_obj

        text_obj.data.font = bpy.data.fonts.load(str(Resources.get_bold_font()))
        text_obj.data.size = 0.02
        text_obj.data.align_x = "LEFT"

        # Create material for text
        mat = bpy.data.materials.new(name=f"Material_{abbrev}")
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        nodes["Principled BSDF"].inputs["Base Color"].default_value = self._hex_to_rgba(
            color
        )

        # Assign material to text
        text_obj.data.materials.append(mat)

        # Link both objects to the main collection
        for obj in [empty_obj, text_obj]:
            for col in obj.users_collection:
                col.objects.unlink(obj)
            self.collection.objects.link(obj)

        return empty_obj

    def _get_offsets_dict(self) -> dict[int, Vector]:
        """Calculate position offsets for each possible position.

        Returns:
            Dict[int, Vector]: Dictionary mapping position numbers to Vector locations

        """
        num_drivers = len(self.driver_abbrevs)
        offsets = {}

        for position in range(1, num_drivers + 1):
            # Calculate vertical offset (top to bottom)
            y_offset = -(position - 1) * self.spacing
            offsets[position] = Vector((0, y_offset, 0))

        return offsets

    @staticmethod
    def _hex_to_rgba(hex_color: str) -> tuple[float, float, float, float]:
        """Convert hex color to RGBA values."""
        hex_color = hex_color.lstrip("#")
        rgb = tuple(int(hex_color[i : i + 2], 16) / 255 for i in (0, 2, 4))
        return (rgb[0], rgb[1], rgb[2], 1.0)  # Add alpha channel
