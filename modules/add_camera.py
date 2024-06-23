from io import StringIO

import bpy
import mathutils
import pandas as pd
import requests


def add_camera(folder_loc):
    camera_collection = bpy.data.collections.new(name="CameraCollection")
    bpy.context.scene.collection.children.link(camera_collection)
    bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children[-1]

    camera_data = bpy.data.cameras.new(name="VideoCamera")
    camera_obj = bpy.data.objects.new(name="VideoCamera", object_data=camera_data)
    bpy.context.collection.objects.link(camera_obj)

    exact_file = f"{folder_loc}/camera.csv"
    response = requests.get(exact_file, auth=("quinn-caverly", "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"))

    data = StringIO(response.text)
    df = pd.read_csv(data, header=0)

    add_keyframes(camera_obj, df)
    bpy.context.scene.camera = camera_obj


# Time,X,Y,Z,RotW,RotX,RotY,RotZ
def add_keyframes(camera_obj, df):
    # iterate through rows of df
    for i in range(len(df)):
        idx = i + 1

        point = (df["X"][i], df["Y"][i], df["Z"][i])

        camera_obj.location = mathutils.Vector(point)
        camera_obj.keyframe_insert(data_path="location", frame=idx)

        # create rot_quat from RotW, RotX, RotY, RotZ
        rot_quat = mathutils.Quaternion((df["RotW"][i], df["RotX"][i], df["RotY"][i], df["RotZ"][i]))

        camera_obj.rotation_euler = rot_quat.to_euler()
        camera_obj.keyframe_insert(data_path="rotation_euler", frame=idx)
