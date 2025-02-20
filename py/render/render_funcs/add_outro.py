import bpy
from mathutils import Vector
import math

from py.utils.logger import log_info
from py.utils.project_structure import INSTAGRAM_ICON_PATH, DISCORD_ICON_PATH, YOUTUBE_ICON_PATH, TIKTOK_ICON_PATH, Resources


class Outro:
    def __init__(self, config, camera_obj, num_frames):
        """Adds social media links and other outro elements at the end of the video."""
        log_info("Initializing Outro...")
        self.config = config
        self.camera_obj = camera_obj
        self.num_frames = num_frames

        # Create a collection to store all outro objects
        self.outro_collection = bpy.data.collections.new("Outro_Elements")
        bpy.context.scene.collection.children.link(self.outro_collection)

        # Create parent empty object
        self.parent_empty = bpy.data.objects.new("Outro_Parent", None)
        self.outro_collection.objects.link(self.parent_empty)
        self.parent_empty.hide_viewport = True
        self.parent_empty.hide_render = True
        self._parent_to_camera(self.camera_obj, self.parent_empty)
        self.parent_empty.scale = Vector((0.05, 0.05, 0.05))

        self.text_material = self._create_text_material()

        self._create_all_outro_elements()

    def _create_text_material(self):
        """Creates a shared white text material."""
        material = bpy.data.materials.new(name="Shared_Text_Material")
        material.use_nodes = True
        nodes = material.node_tree.nodes
        nodes["Principled BSDF"].inputs["Base Color"].default_value = (
            0.95, 0.95, 0.95, 1)
        return material

    def _create_social_element(self, offset: Vector, image_path: str, title: str, platform: str):
        """Creates a social media element with platform icon and username."""
        # Enable import images as planes addon
        bpy.ops.preferences.addon_enable(module="io_import_images_as_planes")

        # Import image as plane
        bpy.ops.import_image.to_plane(files=[{"name": image_path}])
        icon_plane = bpy.context.selected_objects[0]
        icon_plane.name = f"Icon_{platform}"
        # set rotation in degrees
        icon_plane.rotation_euler = Vector(
            (math.radians(180), math.radians(180), math.radians(180)))

        # Create text for username/handle
        text_curve = bpy.data.curves.new(name=f"Text_{platform}", type="FONT")
        text_obj = bpy.data.objects.new(
            name=f"Text_{platform}", object_data=text_curve)
        self.outro_collection.objects.link(text_obj)

        text_obj.data.body = title
        text_obj.data.align_x = "LEFT"
        text_obj.data.align_y = "CENTER"
        text_obj.data.font = bpy.data.fonts.load(Resources.get_main_font())
        text_obj.data.size = 0.5

        # Assign shared text material
        text_obj.data.materials.append(self.text_material)

        # Create empty to group icon and text
        group_empty = bpy.data.objects.new(f"Social_{platform}", None)
        self.outro_collection.objects.link(group_empty)
        group_empty.hide_viewport = True
        group_empty.hide_render = True

        # Parent icon and text to group empty
        icon_plane.parent = group_empty
        text_obj.parent = group_empty

        # Position elements relative to each other
        icon_plane.location = Vector((0, 0, 0))
        text_obj.location = Vector((0.7, 0, 0))  # Offset text to right of icon

        # Parent group to main outro parent and apply offset
        group_empty.parent = self.parent_empty
        group_empty.location = offset

        return group_empty

    def _create_background_plane(self):
        """Creates a semi-transparent black background plane."""
        bpy.ops.mesh.primitive_plane_add(size=10.0)
        bg_plane = bpy.context.active_object
        bg_plane.name = "Outro_Background"

        # Create semi-transparent black material
        bg_mat = bpy.data.materials.new(name="Outro_Background_Material")
        bg_mat.use_nodes = True
        bg_mat.blend_method = 'BLEND'  # Enable transparency
        nodes = bg_mat.node_tree.nodes
        links = bg_mat.node_tree.links
        nodes.clear()

        # Set up principled shader with transparency
        principled = nodes.new('ShaderNodeBsdfPrincipled')
        output = nodes.new('ShaderNodeOutputMaterial')

        # Set to black with transparency
        principled.inputs['Base Color'].default_value = (0, 0, 0, 1)
        principled.inputs['Alpha'].default_value = 0.3

        links.new(principled.outputs[0], output.inputs[0])

        bg_plane.data.materials.append(bg_mat)
        bg_plane.parent = self.parent_empty
        bg_plane.location = Vector((2.8, 0, -1.1))
        bg_plane.scale = Vector((0.9, 1.6, 0))
        return bg_plane

    def _create_bottom_text(self, location: Vector):
        """Creates bottom text element."""
        text_curve = bpy.data.curves.new(name="Bottom_Text", type="FONT")
        text_obj = bpy.data.objects.new("Bottom_Text", object_data=text_curve)
        self.outro_collection.objects.link(text_obj)

        text_obj.data.body = "Uploading every F1 qualifying"
        text_obj.data.align_x = "CENTER"
        text_obj.data.align_y = "CENTER"
        text_obj.data.font = bpy.data.fonts.load(Resources.get_main_font())
        text_obj.data.size = 0.4

        # Assign shared text material
        text_obj.data.materials.append(self.text_material)

        text_obj.parent = self.parent_empty
        text_obj.location = location

        return text_obj

    def _create_all_outro_elements(self):
        """Creates all outro elements with visibility animation."""
        self._create_background_plane()

        # Create social media elements
        cur_loc = Vector((0, -1.5, 0))
        offset = Vector((0, 1.5, 0))

        # Add bottom text at the end
        self._create_bottom_text(cur_loc + Vector((2.8, -2.0, 0)))

        self._create_social_element(
            cur_loc, DISCORD_ICON_PATH, "discord.gg/formula-viz", "discord")

        cur_loc += offset
        self._create_social_element(
            cur_loc, TIKTOK_ICON_PATH, "@formula-viz", "tiktok")

        cur_loc += offset
        self._create_social_element(
            cur_loc, INSTAGRAM_ICON_PATH, "@formula-viz", "instagram")

        cur_loc += offset
        self._create_social_element(
            cur_loc, YOUTUBE_ICON_PATH, "youtube.com/formula-viz", "youtube")

    def _parent_to_camera(self, camera_obj: bpy.types.Object, element_obj) -> None:
        """Parent the outro element to the camera."""
        element_obj.parent = camera_obj
        end_buffer = self.config["render"]["end_buffer_frames"]

        if self.config["render"]["is_shorts_output"]:
            final_position = (-0.14, 0.0, -1)
            start_position = (-0.14, 3.0, -1)
        else:
            # TODO, modify to support 4k landscape mode
            final_position = (0.0, 0.0, -1)
            start_position = (0.0, 5.0, -1)

        # Set initial position
        element_obj.location = Vector(start_position)
        element_obj.keyframe_insert(data_path="location", frame=0)

        element_obj.keyframe_insert(
            data_path="location", frame=self.num_frames - end_buffer)

        # Animate to final position
        element_obj.location = Vector(final_position)
        element_obj.keyframe_insert(
            data_path="location", frame=self.num_frames - end_buffer + 40)

        element_obj.rotation_euler = camera_obj.rotation_euler
