"""Create all drivers and return a dictionary mapping driver abbreviations to their objects given the driver data."""

import os
import time
from typing import Optional

import bpy
import mathutils
import numpy as np
import pandas as pd
from PIL import Image

from py.utils.colors import hex_to_blender_rgb, hex_to_normal_rgb
from py.utils.logger import log_info
from py.utils.models import Driver
from py.utils.project_structure import F1_CAR_BLEND_PATH, RESOURCES_DIR, Resources


def scale_and_position_car(empty_obj: bpy.types.Object):
    # Calculate the bounds of all objects together
    min_x = min_y = min_z = float("inf")
    max_x = max_y = max_z = float("-inf")

    for obj in empty_obj.children:
        # Calculate object bounds in world space
        for v in obj.bound_box:
            world_v = obj.matrix_world @ mathutils.Vector(v)
            min_x = min(min_x, world_v.x)
            max_x = max(max_x, world_v.x)
            min_y = min(min_y, world_v.y)
            max_y = max(max_y, world_v.y)
            min_z = min(min_z, world_v.z)
            max_z = max(max_z, world_v.z)

    # Calculate center of bounds, but keep bottom at z=0
    center_x = (min_x + max_x) / 2
    center_y = (min_y + max_y) / 2
    center_z = min_z  # Set z-offset to min_z to place bottom at z=0

    # Calculate current width and scaling factor
    current_width = max_x - min_x
    scale_factor = 3.0 / current_width if current_width > 0 else 1.0

    for child in empty_obj.children:
        cur_scale = child.scale
        child.scale = (
            cur_scale[0] * scale_factor,
            cur_scale[1] * scale_factor,
            cur_scale[2] * scale_factor,
        )
        cur_loc = child.location
        child.location = (
            (cur_loc[0] - center_x) * scale_factor,
            (cur_loc[1] - center_y) * scale_factor,
            (cur_loc[2] - center_z) * scale_factor,
        )


def create_team_base(team_id: str):
    """Create a base F1 car object that will be used as a template for this team.

    This can cut the memory usage in half for rest of field renders by only using 2 base for each team.
    """
    bpy.ops.object.empty_add(type="PLAIN_AXES")
    empty_obj = bpy.context.object
    if empty_obj is None:
        raise ValueError("Failed to create empty object")

    empty_obj.name = f"Team{team_id}EmptyCar"
    empty_obj.hide_viewport = True
    empty_obj.hide_render = True

    bpy.ops.object.empty_add(type="PLAIN_AXES")
    transform_obj = bpy.context.object
    if transform_obj is None:
        raise ValueError("Failed to create transform object")

    with bpy.data.libraries.load(
        f"{RESOURCES_DIR}/f1-2025-collection/{team_id}.blend"
    ) as (data_from, data_to):
        data_to.objects = data_from.objects

    for obj in data_to.objects:
        obj.parent = empty_obj

        # Iterate through materials to set metallic to 0.5 for principled BSDF nodes
        if obj.material_slots:
            for material_slot in obj.material_slots:
                if material_slot.material and material_slot.material.node_tree:
                    for node in material_slot.material.node_tree.nodes:
                        if node.type == "BSDF_PRINCIPLED":
                            node.inputs["Metallic"].default_value = 0.8

    scale_and_position_car(empty_obj)
    return empty_obj


def create_null_base():
    """Create a base F1 car object that will be used as a template for all drivers."""
    bpy.ops.object.empty_add(type="PLAIN_AXES")
    empty_obj = bpy.context.object
    if empty_obj is None:
        raise ValueError("Failed to create empty object")

    empty_obj.name = "MasterEmptyCar"
    empty_obj.hide_viewport = True
    empty_obj.hide_render = True

    with bpy.data.libraries.load(str(F1_CAR_BLEND_PATH)) as (data_from, data_to):
        data_to.objects = data_from.objects

    for obj in data_to.objects:
        obj.parent = empty_obj

    scale_and_position_car(empty_obj)
    # Im not sure why this is necessary, but this fixes the floating car problem
    for obj in empty_obj.children:
        cur_loc = obj.location
        obj.location = cur_loc + mathutils.Vector((0, 0, -0.8))
    return empty_obj


def create_driver_from_base(driver_abbrev: str, base_empty_obj: bpy.types.Object):
    """Create a driver object by copying the base empty object and its children."""
    # Create a new collection for this driver
    driver_collection = bpy.data.collections.new(f"{driver_abbrev.title()}CarObject")
    bpy.context.scene.collection.children.link(driver_collection)  # pyright: ignore

    # Create a copy of the master empty
    new_empty = base_empty_obj.copy()
    new_empty.name = f"{driver_abbrev.title()}MasterEmpty"
    driver_collection.objects.link(new_empty)

    # Copy all children objects
    for obj in base_empty_obj.children:
        new_obj = obj.copy()
        new_obj.data = obj.data
        new_obj.name = f"{driver_abbrev.title()}CarObject-{obj.name}"
        new_obj.parent = new_empty

        # Only duplicate materials that need color changes
        if obj.material_slots and (
            "chassis" in obj.name.lower() or "wings" in obj.name.lower()
        ):
            new_obj.data = obj.data.copy()  # pyright: ignore
            for i, slot in enumerate(obj.material_slots):
                if slot.material:
                    # Create a deep copy of just the material
                    new_material = slot.material.copy()
                    new_material.name = f"{driver_abbrev.title()}-{slot.material.name}"
                    new_obj.material_slots[i].material = new_material

        driver_collection.objects.link(new_obj)

    return new_empty


# Time,X,Y,Z,RotW,RotX,RotY,RotZ
def add_driver_keyframes(driver_obj, df):
    """Add keyframes to driver object based on dataframe values."""
    # Pre-fetch all the data we'll need to avoid repeated lookups
    x_values = df["X"]
    y_values = df["Y"]
    rot_w = df["RotW"]
    rot_x = df["RotX"]
    rot_y = df["RotY"]
    rot_z = df["RotZ"]

    # Prepare driver keyframes
    driver_loc_keyframes = []
    driver_rot_keyframes = []
    for i in range(len(df)):
        frame = i + 1
        point = mathutils.Vector((x_values[i], y_values[i], 0))

        rot_quat = mathutils.Quaternion((rot_w[i], rot_x[i], rot_y[i], rot_z[i]))
        rot_eul = rot_quat.to_euler()

        driver_loc_keyframes.append((point, frame))
        driver_rot_keyframes.append((rot_eul, frame))

    # Apply driver keyframes in batch
    for point, frame in driver_loc_keyframes:
        driver_obj.location = point
        driver_obj.keyframe_insert(data_path="location", frame=frame)

    for rot_eul, frame in driver_rot_keyframes:
        driver_obj.rotation_euler = rot_eul
        driver_obj.keyframe_insert(data_path="rotation_euler", frame=frame)


def add_driver_trail(driver_obj, df, driver, trail_color, trail_length=60):
    """Create a trailing effect behind a driver object using a series of connected small objects.

    Args:
        driver_obj: The driver's object
        df: DataFrame with position data
        driver: Driver information
        trail_color: Hex color code for the trail
        trail_length: Maximum length of trail in frames

    Returns:
        The parent object for the trail

    """
    # Create a parent empty for the trail
    trail_parent = bpy.data.objects.new(f"{driver.last_name}TrailParent", None)
    bpy.context.scene.collection.objects.link(trail_parent)

    # Create material for trail
    trail_mat = bpy.data.materials.new(name=f"{driver.last_name}TrailMaterial")
    trail_mat.use_nodes = True
    nodes = trail_mat.node_tree.nodes
    links = trail_mat.node_tree.links

    # Setup material nodes
    bsdf = nodes.get("Principled BSDF")
    if not bsdf:
        nodes.clear()
        bsdf = nodes.new(type="ShaderNodeBsdfPrincipled")
        output = nodes.new(type="ShaderNodeOutputMaterial")
        links.new(bsdf.outputs[0], output.inputs[0])

    # Set trail color
    rgb_color = hex_to_blender_rgb(trail_color)
    bsdf.inputs["Base Color"].default_value = (*rgb_color, 1.0)
    bsdf.inputs["Emission Color"].default_value = (*rgb_color, 1.0)
    bsdf.inputs["Emission Strength"].default_value = 1.5
    bsdf.inputs["Alpha"].default_value = 0.7
    trail_mat.blend_method = "BLEND"

    # Pre-fetch position data
    x_values = df["X"].values
    y_values = df["Y"].values

    stride = 1
    overlap = 2

    # Create trail segments (move in steps to reduce the number of objects)
    for i in range(0, len(df), stride):  # Overlap segments for smooth transitions
        start_idx = (i - stride - overlap + 1) % len(df)
        print(f"Start idx: {start_idx}")

        # Create a curve for this segment
        segment_name = f"{driver.last_name}Trail_Segment_{i}"
        segment_data = bpy.data.curves.new(name=segment_name, type="CURVE")
        segment_data.dimensions = "3D"
        segment_data.resolution_u = 8
        segment_data.bevel_depth = 0.08  # Thickness of trail
        segment_obj = bpy.data.objects.new(segment_name, segment_data)
        bpy.context.scene.collection.objects.link(segment_obj)

        # Create a spline for the segment
        spline = segment_data.splines.new("NURBS")
        spline.points.add(stride + overlap)
        end_idx = 0
        for j in range(stride + overlap):
            cur = (start_idx + j) % len(df)
            end_idx = cur
            spline.points[j].co = (x_values[cur], y_values[cur], 0.1, 1)

        print(f"End idx: {end_idx}")

        # Apply material to the segment
        segment_obj.data.materials.append(trail_mat)

        # Parent to the trail parent
        segment_obj.parent = trail_parent

        # Hide segment initially
        segment_obj.hide_render = True
        segment_obj.hide_viewport = True
        segment_obj.keyframe_insert(data_path="hide_render", frame=1)
        segment_obj.keyframe_insert(data_path="hide_viewport", frame=1)

        segment_obj.hide_render = False
        segment_obj.hide_viewport = False
        segment_obj.keyframe_insert(data_path="hide_render", frame=i + 1)
        segment_obj.keyframe_insert(data_path="hide_viewport", frame=i + 1)

    # # Animate visibility of the segments
    # for frame in range(1, total_frames + 1):
    #     trail_start = max(0, frame - trail_length)

    #     # Show/hide segments as needed
    #     for segment_obj, start_idx, end_idx in trail_segments:
    #         # The segment should be visible if it overlaps with the current trail window
    #         visible = start_idx <= frame and end_idx >= trail_start

    #         # Set and keyframe visibility
    #         segment_obj.hide_render = not visible
    #         segment_obj.hide_viewport = not visible
    #         segment_obj.keyframe_insert(data_path="hide_render", frame=frame)
    #         segment_obj.keyframe_insert(data_path="hide_viewport", frame=frame)

    #         # Optional: Adjust opacity based on position in the trail
    #         # This requires material to be unique per segment (make copies if needed)

    return trail_parent


def replace_color_in_image(blender_obj, hex_color, driver):
    """Replace color in image texture node of a material.

    This is done by creating a new image file and by replacing the pixels.
    Using numpy here for faster processing of the pixels.
    """
    material = blender_obj.material_slots[0].material
    if not material.node_tree.nodes:
        raise ValueError(f"Material {material.name} has no nodes.")

    image_node = None
    for node in material.node_tree.nodes:
        if node.type == "TEX_IMAGE":
            image_node = node
            break

    if not image_node:
        raise ValueError(f"Material {material.name} has no image node.")

    image_path = bpy.path.abspath(image_node.image.filepath)
    new_image_path = str(
        Resources.get_new_texture_image_path(blender_obj.name, hex_color)
    )

    # first check if the image already exists
    if os.path.exists(new_image_path):
        new_image = bpy.data.images.load(new_image_path)
        image_node.image = new_image
        return

    # Read image and convert to numpy array
    with Image.open(image_path) as img:
        # Convert image to numpy array for faster processing
        img_array = np.array(img)

        # Define the colors
        old_color = np.array(hex_to_normal_rgb("#FF472C"))
        new_color = np.array(hex_to_normal_rgb(hex_color))

        # Create a mask where pixels match the old color
        # The == comparison will create a boolean array for each color channel
        # All channels must match for a pixel to be replaced
        mask = np.all(img_array == old_color, axis=2)

        # Use the mask to replace the colors
        # This is much faster than pixel-by-pixel operations
        img_array[mask] = new_color

        # Create a new image from the array
        new_img = Image.fromarray(img_array)
        new_img.save(new_image_path)

    # Load the new image into Blender and assign it to the material
    new_image = bpy.data.images.load(new_image_path)
    image_node.image = new_image


def set_color(driver_obj: bpy.types.Object, color: str, driver_abbrev: str):
    """Set color for different parts of the driver's car."""
    for child_obj in driver_obj.children:
        if "chassis" in child_obj.name.lower():
            start_time = time.time()
            replace_color_in_image(child_obj, color, driver_abbrev)
            log_info(
                f"  Time to replace color in chassis: {time.time() - start_time:.2f} seconds"
            )
        if "wings" in child_obj.name.lower():
            # Reset material nodes as it was originally an image and set color
            rgb_color = hex_to_blender_rgb(color)
            if child_obj.material_slots and child_obj.material_slots[0].material:
                material = child_obj.material_slots[0].material

                # Find the principled BSDF node
                bsdf_node = None
                for node in material.node_tree.nodes:  # pyright: ignore
                    if node.type == "BSDF_PRINCIPLED":
                        bsdf_node = node
                        break

                # Find any image texture connected to base color and disconnect it
                for link in material.node_tree.links:  # pyright: ignore
                    if (
                        link.to_node == bsdf_node
                        and link.to_socket.name == "Base Color"  # pyright: ignore
                    ):
                        material.node_tree.links.remove(link)  # pyright: ignore

                # Set the RGB color directly
                bsdf_node.inputs["Base Color"].default_value = (*rgb_color, 1.0)  # pyright: ignore

        if "steering" in child_obj.name.lower():
            child_obj.hide_viewport = True
            child_obj.hide_render = True


def main(
    driver_dfs: dict[Driver, pd.DataFrame],
    drivers: list[Driver],
    driver_colors: list[str],
    quick_textures_mode: bool,
    rest_of_field_focused_driver: Optional[Driver],
) -> dict[Driver, bpy.types.Object]:
    """Process all drivers and return a dictionary mapping driver abbreviations to their objects."""
    quick_textures_mode_max = 2

    base_empty_objs_by_team: dict[str, bpy.types.Object] = {}

    driver_objs: dict[Driver, bpy.types.Object] = {}
    for i, (driver, color) in enumerate(zip(drivers, driver_colors)):
        if quick_textures_mode and i >= quick_textures_mode_max:
            continue

        log_info(f"Adding {i + 1}/{len(drivers)} driver: {driver} in color: {color}")
        start_time = time.time()

        if rest_of_field_focused_driver and driver != rest_of_field_focused_driver:
            if "null" not in base_empty_objs_by_team:
                base_empty_objs_by_team["null"] = create_null_base()
            base_empty_obj = base_empty_objs_by_team["null"]
        elif driver.team in base_empty_objs_by_team:
            base_empty_obj = base_empty_objs_by_team[driver.team]
        else:
            base_empty_obj = create_team_base(driver.team)
            base_empty_objs_by_team[driver.team] = base_empty_obj

        driver_obj = create_driver_from_base(driver.last_name, base_empty_obj)
        if not quick_textures_mode:
            set_color(driver_obj, color, driver.abbrev)
        add_driver_keyframes(driver_obj, driver_dfs[driver])
        # add_driver_trail(driver_obj, driver_dfs[driver], driver, color)

        driver_objs[driver] = driver_obj

        elapsed_time = time.time() - start_time
        log_info(f"Driver {driver} added in {elapsed_time:.2f} seconds")

    return driver_objs
