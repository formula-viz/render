import math

import bpy
import mathutils
import numpy as np
import pandas as pd
from scipy.interpolate import UnivariateSpline


# rgb colors in blender are between 0 and 1, this is expected input
def set_color_by_rgb(obj, color):
    # if obj has no mat at all, we need to create one

    if not obj.data.materials:
        mat = bpy.data.materials.new(name="CustomColorMaterial")
        obj.data.materials.append(mat)
    else:
        mat = obj.data.materials[0]

    mat.use_nodes = True
    nodes = mat.node_tree.nodes

    principled_bsdf = None
    for node in nodes:
        if node.type == "BSDF_PRINCIPLED":
            principled_bsdf = node
            break

    for link in mat.node_tree.links:
        if link.to_node == principled_bsdf and link.to_socket.name == "Base Color":
            mat.node_tree.links.remove(link)

    new_base_color_rgba = (*color, 1.0)
    principled_bsdf.inputs["Base Color"].default_value = new_base_color_rgba


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
def _create_driver_fbx(driver, color):
    driver_collection = bpy.data.collections.new(name=driver.title() + "Collection")
    bpy.context.scene.collection.children.link(driver_collection)
    bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children[-1]

    file_path = "formula-1-2024-generic/source/F1_TexPaintBlender_v01_20210215.fbx"
    bpy.ops.import_scene.fbx(filepath=file_path)

    for obj in bpy.context.selected_objects:
        obj.name = f"{driver.title()}_{obj.name}"

    # scale_to_2_meters(driver_obj)
    # set_color_by_hex(driver_obj, color)

    bpy.ops.object.empty_add(type="PLAIN_AXES")
    empty_obj = bpy.context.object
    empty_obj.name = "MasterEmpty" + driver.title()
    # make this empty_obj invisible
    empty_obj.hide_viewport = True

    wheels_objs = []
    for obj in driver_collection.objects:
        if obj != empty_obj:
            obj.parent = empty_obj

        if "wheel" in obj.name.lower():
            wheels_objs.append(obj)

        for substr in ["chassis", "appliances", "steering", "wings"]:
            if substr in obj.name.lower():
                set_color_by_rgb(obj, color)

    return empty_obj, wheels_objs


# Time,X,Y,Z,RotW,RotX,RotY,RotZ
def add_keyframes(driver_obj, wheels_objs, df):
    for i in range(len(df)):
        idx = i + 1

        point = mathutils.Vector((df["X"][i], df["Y"][i], df["Z"][i]))
        rot_eul = mathutils.Quaternion((df["RotW"][i], df["RotX"][i], df["RotY"][i], df["RotZ"][i])).to_euler()
        harsher_rot_eul = mathutils.Quaternion(
            (df["HarsherRotW"][i], df["HarsherRotX"][i], df["HarsherRotY"][i], df["HarsherRotZ"][i])
        ).to_euler()

        # for the front wheels, get the differences between the z's for harsher and normal, then add the diff to the front wheel rot
        front_wheel_diff = harsher_rot_eul[2] - rot_eul[2]

        wheel_rot = df["TireRot"][i]
        for wheel_obj in wheels_objs:
            rot = wheel_obj.rotation_euler  # the other infos for y, z may change so just grab what already exists first
            rot[0] = wheel_rot

            if "frontwheel" in wheel_obj.name.lower():
                default = -np.pi if wheel_obj.name[-1] == "R" else 0
                rot[2] = default - front_wheel_diff

            wheel_obj.rotation_euler = rot
            wheel_obj.keyframe_insert(data_path="rotation_euler", frame=idx)

        driver_obj.location = point
        driver_obj.keyframe_insert(data_path="location", frame=idx)

        driver_obj.rotation_euler = rot_eul
        driver_obj.keyframe_insert(data_path="rotation_euler", frame=idx)


def add_car_rots(df):
    points = [(df["X"][i], df["Y"][i], df["Z"][i]) for i in range(len(df))]

    def get_rots(points, lookahead_points=20, slerp_val=0.1):
        # Previous rotation quaternion for SLERP
        prev_rot = None
        rot_w = []
        rot_x = []
        rot_y = []
        rot_z = []

        for i, point in enumerate(points):
            # Define how far ahead we look based on available points
            lookahead = min(lookahead_points, len(points) - i - 1)

            combined_pos = mathutils.Vector(point)
            for j in range(1, lookahead + 1):
                combined_pos += mathutils.Vector(points[i + j])

            combined_pos /= lookahead + 1
            direction = combined_pos - mathutils.Vector(point)

            # Calculate rotation to track direction
            rot_quat = direction.to_track_quat("-Y", "Z")

            if prev_rot and rot_quat:
                # Interpolate between previous and current quaternion
                rot_quat = prev_rot.slerp(rot_quat, slerp_val)

            rot_w.append(rot_quat.w)
            rot_x.append(rot_quat.x)
            rot_y.append(rot_quat.y)
            rot_z.append(rot_quat.z)

            # Update previous rotation
            prev_rot = rot_quat

        return rot_w, rot_x, rot_y, rot_z

    rot_w, rot_x, rot_y, rot_z = get_rots(points)
    df["RotW"] = rot_w
    df["RotX"] = rot_x
    df["RotY"] = rot_y
    df["RotZ"] = rot_z

    harsher_rot_w, harsher_rot_x, harsher_rot_y, harsher_rot_z = get_rots(points, lookahead_points=2, slerp_val=0.05)
    df["HarsherRotW"] = harsher_rot_w
    df["HarsherRotX"] = harsher_rot_x
    df["HarsherRotY"] = harsher_rot_y
    df["HarsherRotZ"] = harsher_rot_z

    return df


# for each index, we will have the Speed attached to it
# naturally, the difference between frames here is 1/60 of a second
# so if the speed is 10 m/s, the radius of f1 tire is 0.33 meters


# angular velocity is calculated as v/r where v is linear velocity or 10 m/s for example and r is 0.33 meters
def add_wheel_rots(df):
    prev_rot = 0  # this is arbitrary but shouldnt matter because it is a wheel
    tire_rots = []
    for i in range(len(df)):
        rad_per_s = df["Speed"][i] / 0.33
        new_rot = -(prev_rot + rad_per_s / 60)  # should rotate in negative x, this is arbitrary, relative to the model
        tire_rots.append(new_rot)
        prev_rot = new_rot

    df["TireRot"] = tire_rots
    return df


def get_driver_tel(driver, session):
    _, _, q3 = session.laps.pick_driver(driver).split_qualifying_sessions()
    tel = q3.pick_fastest().get_telemetry(frequency="original")

    # grabs interpolation also because it conveniently inserts the start and finish
    tel = tel[tel["Source"].isin(["pos", "interpolation"])]

    # because we remove indices, we need to reset them
    tel.reset_index(drop=True, inplace=True)

    tel["X"] = tel["X"].apply(lambda x: x / 10)
    tel["Y"] = tel["Y"].apply(lambda y: y / 10)
    tel["Z"] = tel["Z"].apply(lambda z: z / 10)

    return tel


def get_driver_df(tel):
    total_distance = 0
    distances = [0.0]
    for i in range(1, len(tel)):
        point_a = (tel["X"][i - 1], tel["Y"][i - 1])
        point_b = (tel["X"][i], tel["Y"][i])

        distance = ((point_a[0] - point_b[0]) ** 2 + (point_a[1] - point_b[1]) ** 2) ** 0.5
        total_distance += distance
        distances.append(total_distance)

    displacements = distances / total_distance

    # we want to set weights such that the spline is forced to go through the start and end points
    weights = np.ones(len(displacements))
    weights[0] = 1000
    weights[-1] = 1000

    spl_x = UnivariateSpline(displacements, tel["X"], w=weights, s=len(displacements) // 3)
    spl_y = UnivariateSpline(displacements, tel["Y"], w=weights, s=len(displacements) // 3)

    # we want to first smooth the speed data using a spline again
    time_floats = tel["Time"].apply(lambda t: t.total_seconds())
    std_time_floats = time_floats / time_floats.max()

    speed_spline = UnivariateSpline(std_time_floats, tel["Speed"], s=len(time_floats))

    # now, take the max of time floats and multiply it by 60 to get 60hz or 60fps
    frame_count = int(time_floats.max() * 60)

    # now, we want to sample the spline at 60hz
    sampled_speeds = speed_spline(np.linspace(0, 1, frame_count))

    # now that we have speeds, we can use this to get what % of the track is covered at each frame
    d_covered = [0.0]

    sampled_speeds_m_per_s = np.array(sampled_speeds) / 1000 * 60

    # first lets find the total d which will be covered based on the speed
    total_d = 0.0
    for i in sampled_speeds_m_per_s:
        total_d += i  # because each is over 1/60th of a second
        d_covered.append(total_d)

    adj_d_covered = d_covered / total_d

    final_x = spl_x(adj_d_covered)
    final_y = spl_y(adj_d_covered)

    # add the first value to the beginning of sampled_speeds_m_per_s so they match length
    sampled_speeds_m_per_s = np.insert(sampled_speeds_m_per_s, 0, sampled_speeds_m_per_s[0])

    return pd.DataFrame({"X": final_x, "Y": final_y, "Z": np.zeros(len(final_x)), "Speed": sampled_speeds_m_per_s})


def create_path(driver, first_point, color):
    curve_data = bpy.data.curves.new(name=driver.title() + "Path", type="CURVE")
    curve_data.dimensions = "3D"
    polyline = curve_data.splines.new("POLY")

    polyline.points.add(0)
    point = polyline.points[0]
    point.co = (first_point[0], first_point[1], first_point[2], 1)

    curve_object = bpy.data.objects.new(driver.title() + "Path", curve_data)
    bpy.context.collection.objects.link(curve_object)

    curve_object.data.bevel_depth = 0.1
    set_color_by_rgb(curve_object, color)

    return polyline


def create_driver(driver, color, tel):
    driver_obj, wheels_objs = _create_driver_fbx(driver, color)
    df = get_driver_df(tel)
    df = add_car_rots(df)
    df = add_wheel_rots(df)
    add_keyframes(driver_obj, wheels_objs, df)

    polyline = create_path(driver, (df["X"][0], df["Y"][0], df["Z"][0]), color)

    def update_path(scene):
        idx = scene.frame_current
        if idx < len(df):
            pos = (df["X"][idx], df["Y"][idx], df["Z"][idx])

            polyline.points.add(1)
            point = polyline.points[-1]
            point.co = (pos[0], pos[1], pos[2], 1)

    bpy.app.handlers.frame_change_pre.append(update_path)

    return df, driver_obj
