import bpy
from mathutils import Vector
import math

from typing import Optional

from utils.colors import hex_to_blender_rgb
from utils.project_structure import DriverDataPS
from utils.logger import log_info


class DriverCircle:
    def __init__(
        self,
        driver_abbrev: str,
        color: str,  # color will be hex
        driver_car_obj: Optional[bpy.types.Object],
        camera_obj: Optional[bpy.types.Object],
        pre_existing_empty: Optional[bpy.types.Object] = None,
    ):
        self.driver_abbrev = driver_abbrev
        self.driver_car_obj = driver_car_obj
        self.camera_obj = camera_obj
        self.color = color

        log_info(f"Initializing DriverCircle for {driver_abbrev}...")

        if pre_existing_empty:
            self.parent_empty = pre_existing_empty
        else:
            bpy.ops.object.empty_add(type="PLAIN_AXES", location=(0, 0, 0))
            self.parent_empty = bpy.context.active_object
            self.parent_empty.hide_render = True
            self.parent_empty.hide_viewport = True
            self.parent_empty.name = f"{driver_abbrev}CircleParent"

        self._setup()

    def _setup(self):
        self.circle_face = self._create_circle_face()
        outline = self._create_outline()

        # Parent outline to circle face
        outline.parent = self.circle_face
        # Parent circle to empty
        self.circle_face.parent = self.parent_empty

        # if these are not given, then assume this is in isolated mode
        # we will handle the relative parenting later
        if self.camera_obj and self.driver_car_obj:
            # Parent empty to car
            self._parent_to_car()
            # Add track to camera constraint
            self._add_camera_tracking()

    def _create_circle_face(self) -> bpy.types.Object:
        # Create circular face for the image
        bpy.ops.mesh.primitive_circle_add(
            radius=1.0, vertices=32, fill_type="NGON")
        circle_obj = bpy.context.active_object
        circle_obj.name = f"{self.driver_abbrev}CircleFace"

        circle_obj.rotation_euler.z = math.radians(-75)

        # Disable shadow casting, no shadow on the car
        circle_obj.visible_shadow = False
        circle_obj.display.show_shadows = False

        # Create material for the face
        face_mat = bpy.data.materials.new(
            name=f"{self.driver_abbrev}CircleFaceMaterial"
        )
        face_mat.use_nodes = True
        nodes = face_mat.node_tree.nodes
        nodes.clear()

        # Create nodes for image texture
        node_principled = nodes.new("ShaderNodeBsdfPrincipled")
        node_tex = nodes.new("ShaderNodeTexImage")
        node_output = nodes.new("ShaderNodeOutputMaterial")

        # Add UV Map node
        node_uvmap = nodes.new("ShaderNodeUVMap")

        # Load and assign the image
        image_path = DriverDataPS.get_driver_image_path(self.driver_abbrev)
        image = bpy.data.images.load(image_path)
        node_tex.image = image

        # Link nodes
        links = face_mat.node_tree.links
        # UV to Image Texture
        links.new(node_uvmap.outputs[0], node_tex.inputs[0])
        links.new(node_tex.outputs[0], node_principled.inputs[0])  # Color
        links.new(node_principled.outputs[0], node_output.inputs[0])

        # Add material to object
        circle_obj.data.materials.append(face_mat)

        # Ensure proper UV mapping
        bpy.context.view_layer.objects.active = circle_obj
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.uv.unwrap(method="ANGLE_BASED", margin=0.001)
        bpy.ops.object.mode_set(mode="OBJECT")

        return circle_obj

    def _create_outline(self) -> bpy.types.Object:
        # Create torus for the outline
        bpy.ops.mesh.primitive_torus_add(
            major_radius=1.0,  # Radius of the circle
            minor_radius=0.02,  # Thickness of the outline
            major_segments=32,  # Segments of the circle
            minor_segments=8,  # Segments of the tube
        )
        outline = bpy.context.active_object
        outline.name = f"{self.driver_abbrev}CircleOutline"

        # Disable shadow casting, no shadow on the car
        outline.visible_shadow = False
        outline.display.show_shadows = False

        # Create material for the outline
        outline_mat = bpy.data.materials.new(
            name=f"{self.driver_abbrev}CircleOutlineMaterial"
        )
        outline_mat.use_nodes = True
        bsdf = outline_mat.node_tree.nodes["Principled BSDF"]

        bsdf.inputs["Base Color"].default_value = (
            *hex_to_blender_rgb(self.color), 1)
        bsdf.inputs["Metallic"].default_value = 0.8
        bsdf.inputs["Roughness"].default_value = 0.3

        outline.data.materials.append(outline_mat)
        return outline

    def _parent_to_car(self) -> None:
        """Parent the circle to the car and position it above."""
        self.parent_empty.parent = self.driver_car_obj
        self.parent_empty.location = Vector((0, 0, 2.5))

    def _add_camera_tracking(self) -> None:
        """Add constraint to make circle face camera."""
        constraint = self.parent_empty.constraints.new("TRACK_TO")
        constraint.target = self.camera_obj
        constraint.track_axis = "TRACK_Z"
        constraint.up_axis = "UP_Y"
