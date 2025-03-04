"""Create all drivers and return a dictionary mapping driver abbreviations to their objects given the driver data."""

import os
import time

import bpy
import mathutils
import numpy as np
import pandas as pd
from PIL import Image

from py.utils.colors import hex_to_blender_rgb, hex_to_normal_rgb
from py.utils.logger import log_info
from py.utils.models import Driver
from py.utils.project_structure import F1_CAR_BLEND_PATH, Resources


def create_base_driver_obj():
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
) -> dict[Driver, bpy.types.Object]:
    """Process all drivers and return a dictionary mapping driver abbreviations to their objects."""
    quick_textures_mode_max = 2

    base_empty_obj = create_base_driver_obj()

    driver_objs: dict[Driver, bpy.types.Object] = {}
    for i, (driver, color) in enumerate(zip(drivers, driver_colors)):
        if quick_textures_mode and i >= quick_textures_mode_max:
            continue

        log_info(f"Adding {i + 1}/{len(drivers)} driver: {driver} in color: {color}")
        start_time = time.time()

        driver_obj = create_driver_from_base(driver.last_name, base_empty_obj)
        if not quick_textures_mode:
            set_color(driver_obj, color, driver.abbrev)
        add_driver_keyframes(driver_obj, driver_dfs[driver])

        driver_objs[driver] = driver_obj

        elapsed_time = time.time() - start_time
        log_info(f"Driver {driver} added in {elapsed_time:.2f} seconds")

    return driver_objs
