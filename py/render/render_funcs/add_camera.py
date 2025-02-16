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


# move along the vector between cam_df and car_df, ensuring we are at most max_distance away
def move_with_min_distance(cam_df, car_df, max_distance):
    for i in range(len(cam_df)):
        cam_point = (cam_df["X"][i], cam_df["Y"][i], cam_df["Z"][i])
        car_point = (car_df["X"][i], car_df["Y"][i], car_df["Z"][i])

        vector = mathutils.Vector(cam_point) - mathutils.Vector(car_point)

        if vector.length > max_distance:
            cam_df.loc[i, "X"] = car_df["X"][i] + \
                vector.normalized().x * max_distance
            cam_df.loc[i, "Y"] = car_df["Y"][i] + \
                vector.normalized().y * max_distance
            cam_df.loc[i, "Z"] = car_df["Z"][i] + \
                vector.normalized().z * max_distance


# Time,X,Y,Z,RotW,RotX,RotY,RotZ
# before the car is actually on the run, after hitting the start/finish and before hitting it again
# the camera will point at the line, this will be a good visual indication for the viewer that
# the run hasn't started
def add_keyframes(
    camera_obj, cam_df, driver_df, start_buffer_frames, end_buffer_frames
):
    assert len(cam_df) == len(driver_df)

    # iterate through rows of df
    for i in range(len(cam_df)):
        frame = i + 1

        camera_point = (cam_df["X"][i], cam_df["Y"][i], cam_df["Z"][i])

        if start_buffer_frames <= frame <= len(cam_df) - end_buffer_frames:
            look_at_point = mathutils.Vector((
                driver_df["X"][i],
                driver_df["Y"][i],
                driver_df["Z"][i],
            ))
        elif frame < start_buffer_frames:
            look_at_point = mathutils.Vector((
                driver_df["X"][start_buffer_frames - 1],
                driver_df["Y"][start_buffer_frames - 1],
                driver_df["Z"][start_buffer_frames - 1],
            ))
        else:  # frame > end_buffer_frames
            camera_point = (
                cam_df["X"][len(cam_df) - end_buffer_frames - 1],
                cam_df["Y"][len(cam_df) - end_buffer_frames - 1],
                cam_df["Z"][len(cam_df) - end_buffer_frames - 1],
            )
            look_at_point = mathutils.Vector((
                driver_df["X"][len(cam_df) - end_buffer_frames - 1],
                driver_df["Y"][len(cam_df) - end_buffer_frames - 1],
                driver_df["Z"][len(cam_df) - end_buffer_frames - 1],
            ))

        camera_obj.location = mathutils.Vector(camera_point)
        camera_obj.keyframe_insert(data_path="location", frame=frame)

        direction = look_at_point - camera_obj.location
        rot_quat = direction.to_track_quat("-Z", "Y")

        camera_obj.rotation_mode = "QUATERNION"
        camera_obj.rotation_quaternion = rot_quat
        camera_obj.keyframe_insert(
            data_path="rotation_quaternion", frame=frame)


# df for cam is the df used to create the keyframes for the driver obj passed
# we will create the camera path using these driver points and then point the
# camera towards the driver object
def main(df_for_cam, driver_obj, max_distance, start_buffer_frames, end_buffer_frames):
    camera_collection = bpy.data.collections.new(name="CameraCollection")
    bpy.context.scene.collection.children.link(camera_collection)
    bpy.context.view_layer.active_layer_collection = (
        bpy.context.view_layer.layer_collection.children[-1]
    )

    camera_data = bpy.data.cameras.new(name="VideoCamera")
    camera_obj = bpy.data.objects.new(
        name="VideoCamera", object_data=camera_data)
    bpy.context.collection.objects.link(camera_obj)

    cam_df = scale_frames(df_for_cam)
    move_with_min_distance(cam_df, df_for_cam, max_distance)

    add_keyframes(
        camera_obj, cam_df, df_for_cam, start_buffer_frames, end_buffer_frames
    )

    bpy.context.scene.camera = camera_obj
    return camera_obj
