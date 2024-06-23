import bpy
import mathutils
import numpy as np
import pandas as pd
from scipy.interpolate import UnivariateSpline


# rgb colors in blender are between 0 and 1, this is expected input
def set_color_by_rgb(obj, color):
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

    for obj in driver_collection.objects:
        if obj != empty_obj:
            obj.parent = empty_obj

        for substr in ["chassis", "appliances", "steering", "wings"]:
            if substr in obj.name.lower():
                set_color_by_rgb(obj, color)

    return empty_obj


# Time,X,Y,Z,RotW,RotX,RotY,RotZ
def add_keyframes(driver_obj, df):
    for i in range(len(df)):
        idx = i + 1

        point = mathutils.Vector((df["X"][i], df["Y"][i], df["Z"][i]))
        rot_quat = mathutils.Quaternion((df["RotW"][i], df["RotX"][i], df["RotY"][i], df["RotZ"][i]))

        driver_obj.location = point
        driver_obj.keyframe_insert(data_path="location", frame=idx)

        driver_obj.rotation_euler = rot_quat.to_euler()
        driver_obj.keyframe_insert(data_path="rotation_euler", frame=idx)


def add_car_rots(df):
    points = [(df["X"][i], df["Y"][i], df["Z"][i]) for i in range(len(df))]

    # Previous rotation quaternion for SLERP
    prev_rot = None
    rot_w = []
    rot_x = []
    rot_y = []
    rot_z = []

    for i, point in enumerate(points):
        # Define how far ahead we look based on available points
        lookahead = min(20, len(points) - i - 1)

        combined_pos = mathutils.Vector(point)
        for j in range(1, lookahead + 1):
            combined_pos += mathutils.Vector(points[i + j])

        combined_pos /= lookahead + 1
        direction = combined_pos - mathutils.Vector(point)

        # Calculate rotation to track direction
        rot_quat = direction.to_track_quat("-Y", "Z")

        if prev_rot and rot_quat:
            # Interpolate between previous and current quaternion
            rot_quat = prev_rot.slerp(rot_quat, 0.1)

        rot_w.append(rot_quat.w)
        rot_x.append(rot_quat.x)
        rot_y.append(rot_quat.y)
        rot_z.append(rot_quat.z)

        # Update previous rotation
        prev_rot = rot_quat

    df["RotW"] = rot_w
    df["RotX"] = rot_x
    df["RotY"] = rot_y
    df["RotZ"] = rot_z

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

    spl_x = UnivariateSpline(displacements, tel["X"], w=weights, s=len(displacements) // 2)
    spl_y = UnivariateSpline(displacements, tel["Y"], w=weights, s=len(displacements) // 2)

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

    return pd.DataFrame({"X": final_x, "Y": final_y, "Z": np.zeros(len(final_x))})


def create_driver(driver_obj, tel):
    df = get_driver_df(tel)
    df = add_car_rots(df)
    add_keyframes(driver_obj, df)

    return len(df), df


def create_drivers_and_cam(drivers, colors, session):
    driver_tels = [get_driver_tel(driver, session) for driver in drivers]

    # fastf1 interpolates the start/finish line for the car but it is independent of the other cars
    # the problem is that the start/finish will probably be put in a different place for each car.
    # to solve this, we can just take all the drivers we have, average their start/finish line, then
    # make it so that every driver has the same start/finish. This means the start/finish will be different
    # for dif runs on the same track but this does not really matter.
    mean_x = np.mean([tel["X"].iloc[0] for tel in driver_tels])
    mean_y = np.mean([tel["Y"].iloc[0] for tel in driver_tels])
    for tel in driver_tels:
        tel["X"].iloc[0] = mean_x
        tel["Y"].iloc[0] = mean_y

    mean_x = np.mean([tel["X"].iloc[-1] for tel in driver_tels])
    mean_y = np.mean([tel["Y"].iloc[-1] for tel in driver_tels])
    for tel in driver_tels:
        tel["X"].iloc[-1] = mean_x
        tel["Y"].iloc[-1] = mean_y

    frames = []
    df_for_cam, driver_obj = None, None
    for driver, color, tel in zip(drivers, colors, driver_tels):
        driver_obj = _create_driver_fbx(driver, color)
        d_frames, df = create_driver(driver_obj, tel)

        frames.append(d_frames)
        if driver == drivers[0]:
            df_for_cam, driver_obj = df, driver_obj

    return max(frames), df_for_cam, driver_obj
