from io import StringIO

import bpy
import mathutils
import pandas as pd
import requests


def set_color_by_hex(driver_obj, hex_color):
    # Convert hex color to RGB (values between 0 and 1)
    r, g, b = tuple(int(hex_color[i : i + 2], 16) / 255.0 for i in (1, 3, 5))

    # Create a new material
    material = bpy.data.materials.new(name="CustomColorMaterial")
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (r, g, b, 1)  # Set the color

    # Assign the material to the object
    if not driver_obj.data.materials:
        driver_obj.data.materials.append(material)
    else:
        # Optionally replace existing materials
        driver_obj.data.materials[0] = material


def scale_to_2_meters(driver_obj):
    # we need to find the dimensions of the object and then scale it so that the width is 2 meters
    # the z should be the smallest, then there will be a height and width which might be either
    # x or y. we will just find the differences between max and min of each dimension and find
    # the middle difference, the axis corresponding to the middle difference will be the width
    # then find the scale to create 2 meters

    # get difference in x, y, z
    x_diff = driver_obj.dimensions[0]
    y_diff = driver_obj.dimensions[1]
    z_diff = driver_obj.dimensions[2]

    # find the middle difference
    diffs = [x_diff, y_diff, z_diff]
    diffs.sort()
    middle_diff = diffs[1]

    # find the scale
    scale = 2 / middle_diff

    driver_obj.scale = [scale, scale, scale]


# this should eventually consider more information like maybe the driver's nationality
# or team to color the car differently based on various factors
def _create_driver_fbx(driver, color="#0000FF"):

    file_path = "f1-car.fbx"
    bpy.ops.import_scene.fbx(filepath=file_path)
    driver_obj = bpy.data.objects["f1-car"]
    driver_obj.name = driver.title() + "Driver"

    scale_to_2_meters(driver_obj)
    set_color_by_hex(driver_obj, color)

    return driver_obj


# Time,X,Y,Z,RotW,RotX,RotY,RotZ
def add_keyframes(driver_obj, df):
    # iterate through rows of df
    for i in range(len(df)):
        idx = i + 1

        point = (df["X"][i], df["Y"][i], df["Z"][i])

        driver_obj.location = mathutils.Vector(point)
        driver_obj.keyframe_insert(data_path="location", frame=idx)

        # create rot_quat from RotW, RotX, RotY, RotZ
        rot_quat = mathutils.Quaternion((df["RotW"][i], df["RotX"][i], df["RotY"][i], df["RotZ"][i]))

        driver_obj.rotation_euler = rot_quat.to_euler()
        driver_obj.keyframe_insert(data_path="rotation_euler", frame=idx)


def create_drivers(drivers, folder_loc):
    car_collection = bpy.data.collections.new(name="CarCollection")
    bpy.context.scene.collection.children.link(car_collection)
    bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children[-1]

    for i, driver in enumerate(drivers):
        driver_obj = _create_driver_fbx(driver, "#FF0000")
        # we need to load the car path data csv into a df
        exact_file = f"{folder_loc}/{driver}.csv"
        response = requests.get(exact_file, auth=("quinn-caverly", "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"))

        data = StringIO(response.text)
        df = pd.read_csv(data, header=0)

        add_keyframes(driver_obj, df)

        if i == len(drivers) - 1:
            return len(df)
