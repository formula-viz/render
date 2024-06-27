from io import StringIO

import bpy
import mathutils
import numpy as np
import pandas as pd


def scale_frames(df_for_cam):
    scale_factor = 0.8
    z_up = 50

    cam_x = df_for_cam["X"] * scale_factor
    cam_y = df_for_cam["Y"] * scale_factor

    cam_x = cam_x + df_for_cam["X"].mean() - cam_x.mean()
    cam_y = cam_y + df_for_cam["Y"].mean() - cam_y.mean()

    cam_z = np.zeros(len(cam_x)) + z_up

    return pd.DataFrame({"X": cam_x, "Y": cam_y, "Z": cam_z})


# df for cam is the final, already interpolated frames
def add_camera(df_for_cam, driver_obj):
    camera_collection = bpy.data.collections.new(name="CameraCollection")
    bpy.context.scene.collection.children.link(camera_collection)
    bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children[-1]

    camera_data = bpy.data.cameras.new(name="VideoCamera")
    camera_obj = bpy.data.objects.new(name="VideoCamera", object_data=camera_data)
    bpy.context.collection.objects.link(camera_obj)

    cam_df = scale_frames(df_for_cam)

    add_keyframes(camera_obj, cam_df)

    camera_obj.constraints.new(type="TRACK_TO")
    camera_obj.constraints["Track To"].target = driver_obj

    bpy.context.scene.camera = camera_obj


# Time,X,Y,Z,RotW,RotX,RotY,RotZ
def add_keyframes(camera_obj, df):
    # iterate through rows of df
    for i in range(len(df)):
        idx = i + 1

        point = (df["X"][i], df["Y"][i], df["Z"][i])

        camera_obj.location = mathutils.Vector(point)
        camera_obj.keyframe_insert(data_path="location", frame=idx)
