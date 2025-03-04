"""Create a camera that tracks the driver.

Follows a path which is a scaled version of the driver's path, accounted for correct distance.
"""

import bpy
import mathutils
import numpy as np
import pandas as pd

MIN_CAM_DISTANCE = 80
MAX_CAM_DISTANCE = 80


def scale_frames(df_for_cam):
    """Scales the camera positions based on the input DataFrame.

    Args:
        df_for_cam (DataFrame): DataFrame containing position data (X, Y, Z)

    Returns:
        DataFrame: A new DataFrame with scaled X and Y coordinates and fixed Z height

    """
    scale_factor = 0.8
    z_up = 50

    cam_x = df_for_cam["X"] * scale_factor
    cam_y = df_for_cam["Y"] * scale_factor

    cam_x = cam_x + df_for_cam["X"].mean() - cam_x.mean()
    cam_y = cam_y + df_for_cam["Y"].mean() - cam_y.mean()

    cam_z = np.zeros(len(cam_x)) + z_up

    return pd.DataFrame({"X": cam_x, "Y": cam_y, "Z": cam_z})


def move_with_min_max_distance(cam_df, car_df):
    """Adjust camera position to maintain a distance from the car between min_distance and max_distance.

    Args:
        cam_df (DataFrame): DataFrame containing camera position data (X, Y, Z)
        car_df (DataFrame): DataFrame containing car position data (X, Y, Z)

    """
    for i in range(len(cam_df)):
        cam_point = (cam_df["X"][i], cam_df["Y"][i], cam_df["Z"][i])
        car_point = (car_df["X"][i], car_df["Y"][i], car_df["Z"][i])

        vector = mathutils.Vector(cam_point) - mathutils.Vector(car_point)

        # Ensure camera is not too far away
        if vector.length > MAX_CAM_DISTANCE:
            cam_df.loc[i, "X"] = (
                car_df["X"][i] + vector.normalized().x * MAX_CAM_DISTANCE
            )
            cam_df.loc[i, "Y"] = (
                car_df["Y"][i] + vector.normalized().y * MAX_CAM_DISTANCE
            )
            cam_df.loc[i, "Z"] = (
                car_df["Z"][i] + vector.normalized().z * MAX_CAM_DISTANCE
            )

        # Ensure camera is not too close
        elif vector.length < MIN_CAM_DISTANCE:
            cam_df.loc[i, "X"] = (
                car_df["X"][i] + vector.normalized().x * MIN_CAM_DISTANCE
            )
            cam_df.loc[i, "Y"] = (
                car_df["Y"][i] + vector.normalized().y * MIN_CAM_DISTANCE
            )
            cam_df.loc[i, "Z"] = (
                car_df["Z"][i] + vector.normalized().z * MIN_CAM_DISTANCE
            )


def add_keyframes(
    camera_obj, cam_df, driver_df, start_buffer_frames, end_buffer_frames
):
    """Add keyframes to animate a camera following a driver object.

    Before the car is actually on the run, after hitting the start/finish and before hitting it again,
    the camera will point at the line, providing a visual indication for the viewer that the run hasn't started.

    Args:
        camera_obj (Object): The Blender camera object to animate
        cam_df (DataFrame): DataFrame containing camera position data (X, Y, Z)
        driver_df (DataFrame): DataFrame containing driver position data (X, Y, Z)
        start_buffer_frames (int): Number of frames at the start before the main animation begins
        end_buffer_frames (int): Number of frames at the end after the main animation ends

    """
    assert len(cam_df) == len(driver_df)

    # iterate through rows of df
    for i in range(len(cam_df)):
        frame = i + 1

        camera_point = (cam_df["X"][i], cam_df["Y"][i], cam_df["Z"][i])

        if start_buffer_frames <= frame <= len(cam_df) - end_buffer_frames:
            look_at_point = mathutils.Vector(
                (
                    driver_df["X"][i],
                    driver_df["Y"][i],
                    driver_df["Z"][i],
                )
            )
        elif frame < start_buffer_frames:
            look_at_point = mathutils.Vector(
                (
                    driver_df["X"][start_buffer_frames - 1],
                    driver_df["Y"][start_buffer_frames - 1],
                    driver_df["Z"][start_buffer_frames - 1],
                )
            )
        else:  # frame > end_buffer_frames
            camera_point = (
                cam_df["X"][len(cam_df) - end_buffer_frames - 1],
                cam_df["Y"][len(cam_df) - end_buffer_frames - 1],
                cam_df["Z"][len(cam_df) - end_buffer_frames - 1],
            )
            look_at_point = mathutils.Vector(
                (
                    driver_df["X"][len(cam_df) - end_buffer_frames - 1],
                    driver_df["Y"][len(cam_df) - end_buffer_frames - 1],
                    driver_df["Z"][len(cam_df) - end_buffer_frames - 1],
                )
            )

        camera_obj.location = mathutils.Vector(camera_point)
        camera_obj.keyframe_insert(data_path="location", frame=frame)

        direction = look_at_point - camera_obj.location
        rot_quat = direction.to_track_quat("-Z", "Y")

        camera_obj.rotation_mode = "QUATERNION"
        camera_obj.rotation_quaternion = rot_quat
        camera_obj.keyframe_insert(data_path="rotation_quaternion", frame=frame)


def main(df_for_cam, driver_obj, start_buffer_frames, end_buffer_frames):
    """Create a camera that tracks the driver.

    Args:
        df_for_cam (DataFrame): DataFrame containing position data used for camera path
        driver_obj (Object): The Blender object that the camera will follow/look at
        start_buffer_frames (int): Number of frames at the start before the main animation begins
        end_buffer_frames (int): Number of frames at the end after the main animation ends

    Returns:
        Object: The created camera object

    """
    camera_collection = bpy.data.collections.new(name="CameraCollection")

    bpy.context.scene.collection.children.link(camera_collection)  # pyright: ignore
    bpy.context.view_layer.active_layer_collection = (  # pyright: ignore
        bpy.context.view_layer.layer_collection.children[-1]  # pyright: ignore
    )

    camera_data = bpy.data.cameras.new(name="VideoCamera")
    camera_obj = bpy.data.objects.new(name="VideoCamera", object_data=camera_data)
    bpy.context.collection.objects.link(camera_obj)  # pyright: ignore

    cam_df = scale_frames(df_for_cam)
    move_with_min_max_distance(cam_df, df_for_cam)

    add_keyframes(
        camera_obj, cam_df, df_for_cam, start_buffer_frames, end_buffer_frames
    )

    bpy.context.scene.camera = camera_obj  # pyright: ignore
    return camera_obj
