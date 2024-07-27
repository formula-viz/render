import bpy
import mathutils
import pandas as pd
from fastf1 import plotting


def set_color(obj, hex_color: str):
    # Convert hex color to RGB (values between 0 and 1)
    r, g, b = tuple(int(hex_color[i : i + 2], 16) / 255.0 for i in (1, 3, 5))

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

    principled_bsdf.inputs["Base Color"].default_value = (r, g, b, 1)


def create_driver_fbx(driver, hex_color):
    driver_collection = bpy.data.collections.new(name=driver.title() + "Collection")
    bpy.context.scene.collection.children.link(driver_collection)
    bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children[-1]

    file_path = "resources/cars/formula-1-2024-generic/source/F1_TexPaintBlender_v01_20210215.fbx"
    bpy.ops.import_scene.fbx(filepath=file_path)

    for obj in bpy.context.selected_objects:
        obj.name = f"{driver.title()}_{obj.name}"

    bpy.ops.object.empty_add(type="PLAIN_AXES")
    empty_obj = bpy.context.object
    empty_obj.name = "MasterEmpty" + driver.title()
    # make this empty_obj invisible
    empty_obj.hide_viewport = True

    wheels_objs = []
    for obj in driver_collection.objects:
        if obj != empty_obj:
            obj.parent = empty_obj

        if "wheel" in obj.name.lower() and "steering" not in obj.name.lower():
            wheels_objs.append(obj)

        for substr in ["chassis", "appliances", "steering", "wings"]:
            if substr in obj.name.lower():
                set_color(obj, hex_color)

        if "steering" in obj.name.lower():
            # we want to set this invisible for now
            obj.hide_viewport = True
            obj.hide_render = True

    return empty_obj, wheels_objs


# Time,X,Y,Z,RotW,RotX,RotY,RotZ
def add_keyframes(driver_obj, wheels_objs, df):
    for i in range(len(df)):
        idx = i + 1

        # point = mathutils.Vector((df["X"][i], df["Y"][i], df["Z"][i]))
        # TODO: for now setting all z to 0 because cars appear to be under the track
        point = mathutils.Vector((df["X"][i], df["Y"][i], 0))

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

            # TODO: I need to remove the front wheel physics for now because it is janky
            # if "frontwheel" in wheel_obj.name.lower():
            #     default = -np.pi if wheel_obj.name[-1] == "R" else 0
            #     rot[2] = default - front_wheel_diff

            wheel_obj.rotation_euler = rot
            wheel_obj.keyframe_insert(data_path="rotation_euler", frame=idx)

        driver_obj.location = point
        driver_obj.keyframe_insert(data_path="location", frame=idx)

        driver_obj.rotation_euler = rot_eul
        driver_obj.keyframe_insert(data_path="rotation_euler", frame=idx)


def create_driver(driver, hex_color, df):
    driver_obj, wheels_objs = create_driver_fbx(driver, hex_color)
    add_keyframes(driver_obj, wheels_objs, df)

    return driver_obj


def main(year: str, track: str, fps: str, driver_tuples):
    # year, track, fps simply uniquely define the save location
    main_dir = "data/car_data"
    cur_dir = f"{main_dir}/{year}_{track}_{fps}"

    driver_dfs = {}
    for driver_tuple in driver_tuples:
        name, color = driver_tuple
        driver_dfs[name] = pd.read_csv(f"{cur_dir}/{name}.csv")

    # TODO: I am going to experiment with using the ff1 colors for the drivers
    # if this produces sensible results then it is the best plan long term
    driver_objs = {}
    for driver in driver_dfs:
        hex_color = plotting.DRIVER_COLORS[plotting.DRIVER_TRANSLATE[driver]]
        driver_objs[driver] = create_driver(driver, hex_color, driver_dfs[driver])

    return driver_objs, driver_dfs
