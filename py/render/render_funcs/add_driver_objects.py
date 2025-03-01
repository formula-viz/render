"""Create all drivers and return a dictionary mapping driver abbreviations to their objects given the driver data."""

import time

import bpy
import mathutils
import numpy as np
from PIL import Image

from py.utils.colors import hex_to_blender_rgb, hex_to_normal_rgb
from py.utils.logger import log_info
from py.utils.project_structure import F1_CAR_BLEND_PATH, Resources


def create_driver_obj(driver):
    """Create a driver object by loading the F1 car collection and linking it to the scene."""
    with bpy.data.libraries.load(F1_CAR_BLEND_PATH) as (data_from, data_to):
        data_to.collections = ["f1-car-gerulf"]

    driver_collection = data_to.collections[0]
    # ensure collection is linked to the scene
    if driver_collection.name not in bpy.context.scene.collection.children:  # pyright: ignore
        bpy.context.scene.collection.children.link(driver_collection)  # pyright: ignore

    # Set the driver collection as the active collection
    layer_collection = bpy.context.view_layer.layer_collection  # pyright: ignore
    for child in layer_collection.children:
        if child.collection == driver_collection:
            bpy.context.view_layer.active_layer_collection = child  # pyright: ignore
            break

    # Rename the collection to match the driver
    driver_collection.name = f"{driver.title()}CarObject"  # pyright: ignore

    bpy.ops.object.empty_add(type="PLAIN_AXES")
    empty_obj = bpy.context.object
    if empty_obj is None:
        raise ValueError("Failed to create empty object")

    empty_obj.name = f"{driver.title()}MasterEmpty"
    empty_obj.hide_viewport = True
    empty_obj.hide_render = True

    if empty_obj.name not in driver_collection.objects:  # pyright: ignore
        driver_collection.objects.link(empty_obj)  # pyright: ignore

    for obj in driver_collection.objects:  # pyright: ignore
        if obj != empty_obj:
            obj.name = f"{driver.title()}CarObject-{obj.name}"
            obj.parent = empty_obj

    return empty_obj


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
    new_image_path = Resources.get_new_texture_image_path(driver, blender_obj.name)

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


def set_color(driver_obj, color, driver):
    """Set color for different parts of the driver's car."""
    for child_obj in driver_obj.children:
        if "chassis" in child_obj.name.lower():
            start_time = time.time()
            replace_color_in_image(child_obj, color, driver)
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
                for node in material.node_tree.nodes:
                    if node.type == "BSDF_PRINCIPLED":
                        bsdf_node = node
                        break

                # Find any image texture connected to base color and disconnect it
                for link in material.node_tree.links:
                    if (
                        link.to_node == bsdf_node
                        and link.to_socket.name == "Base Color"
                    ):
                        material.node_tree.links.remove(link)

                # Set the RGB color directly
                bsdf_node.inputs["Base Color"].default_value = (*rgb_color, 1.0)  # pyright: ignore

        if "steering" in child_obj.name.lower():
            child_obj.hide_viewport = True
            child_obj.hide_render = True


def main(
    driver_dfs, drivers, driver_colors, quick_textures_mode: bool
) -> dict[str, bpy.types.Object]:
    """Process all drivers and return a dictionary mapping driver abbreviations to their objects."""
    quick_textures_mode_max = 2

    driver_objs = {}
    for i, (driver, color) in enumerate(zip(drivers, driver_colors)):
        if quick_textures_mode and i >= quick_textures_mode_max:
            continue

        log_info(f"Adding {i + 1}/{len(drivers)} driver: {driver} in color: {color}")
        start_time = time.time()

        driver_obj = create_driver_obj(driver)
        if not quick_textures_mode:
            set_color(driver_obj, color, driver)
        add_driver_keyframes(driver_obj, driver_dfs[driver])

        driver_objs[driver] = driver_obj

        elapsed_time = time.time() - start_time
        log_info(f"Driver {driver} added in {elapsed_time:.2f} seconds")

    return driver_objs
