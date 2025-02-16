import math

import bpy  # pyright: ignore
import mathutils  # pyright: ignore
import PIL.Image as Image
from utils.colors import hex_to_blender_rgb, hex_to_normal_rgb
from utils.logger import log_info, log_warn
from utils.project_structure import Resources


def import_crown():
    crown_path = ( Resources.get_crown_path()
    )  # You'll need to add this method to your Resources class
    bpy.ops.import_scene.gltf(filepath=crown_path)
    # Get the imported crown object
    for obj in bpy.context.selected_objects:
        if "crown" in obj.name.lower():
            return obj
    return None


def set_color(obj, rgb_color: tuple[float, float, float]):
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

    principled_bsdf.inputs["Base Color"].default_value = (*rgb_color, 1)


def replace_color_in_image(blender_obj, hex_color, driver_abbrev):
    material = blender_obj.material_slots[0].material
    if not material.node_tree.nodes:
        log_warn(f"Material {material.name} has no nodes.")
        return

    image_node = None
    for node in material.node_tree.nodes:
        if node.type == "TEX_IMAGE":
            image_node = node
            break

    image_path = bpy.path.abspath(image_node.image.filepath)
    new_image_path = Resources.get_new_texture_image_path(
        driver_abbrev, blender_obj.name
    )

    with Image.open(image_path) as img:
        if img.mode != "RGB":
            img = img.convert("RGB")

        width, height = img.size
        new_img = Image.new("RGB", (width, height))

        pixels = img.load()
        new_pixels = new_img.load()

        # this is hardcoded for the fbx file, this is fine to hardcode here
        old_color = hex_to_normal_rgb("#FF472C")
        new_color = hex_to_normal_rgb(hex_color)

        for x in range(width):
            for y in range(height):
                if pixels[x, y] == old_color:
                    new_pixels[x, y] = new_color
                else:
                    new_pixels[x, y] = pixels[x, y]

        new_img.save(new_image_path)

    # Load the new image into Blender and assign it to the material
    new_image = bpy.data.images.load(new_image_path)
    image_node.image = new_image


def load_base_car_fbx():
    """Load the car FBX once and return an empty object which is the parent of the individual objs"""
    # Create a temporary collection to store the base objects
    base_collection = bpy.data.collections.new(name="BaseCarCollection")
    bpy.context.scene.collection.children.link(base_collection)
    bpy.context.view_layer.active_layer_collection = (
        bpy.context.view_layer.layer_collection.children[-1]
    )

    # Import the FBX into this collection
    bpy.ops.import_scene.fbx(filepath=Resources.get_car_fbx_path())
    bpy.ops.file.find_missing_files(directory=Resources.get_car_textures_dir())

    bpy.ops.object.empty_add(type="PLAIN_AXES")
    empty_obj = bpy.context.object
    empty_obj.name = "MasterEmpty"
    # make this empty_obj invisible
    empty_obj.hide_viewport = True

    for obj in base_collection.objects:
        if obj != empty_obj:
            obj.parent = empty_obj

        # move them forward, because the data from fastf1 likely represents the front of the car
        # this way, when we have the car passing the line, it is the tip of the nose passing
        # obj.location[1] += 3.3

    # crown_obj = import_crown()
    # if crown_obj:
    #     crown_obj.parent = empty_obj
    # else:
    #     log_err("Couldn't import the crown object.")

    return empty_obj, base_collection


def create_driver_fbx(driver, hex_color, empty_obj):
    """Create a new driver instance by duplicating base objects"""
    driver_collection = bpy.data.collections.new(
        name=driver.title() + "Collection")
    bpy.context.scene.collection.children.link(driver_collection)
    bpy.context.view_layer.active_layer_collection = (
        bpy.context.view_layer.layer_collection.children[-1]
    )

    new_empty = empty_obj.copy()
    new_empty.name = "MasterEmpty" + driver.title()
    driver_collection.objects.link(new_empty)

    wheels_objs = []
    for child in empty_obj.children_recursive:
        # the cameras get added to the empty for some reason, just remove them
        if child.type == "CAMERA":
            continue

        obj = child.copy()
        if child.data:
            obj.data = child.data.copy()
            # Deep copy materials
            if isinstance(obj.data, bpy.types.Mesh) and obj.data.materials:
                for i, mat in enumerate(obj.data.materials):
                    if mat:
                        new_mat = mat.copy()
                        obj.data.materials[i] = new_mat

        obj.name = f"{driver.title()}_{child.name}"
        driver_collection.objects.link(obj)

        obj.parent = new_empty
        # Maintain original transformation
        obj.matrix_local = child.matrix_local.copy()

        if "wheel" in obj.name.lower() and "steering" not in obj.name.lower():
            wheels_objs.append(obj)
        if "chassis" in obj.name.lower():
            replace_color_in_image(obj, hex_color, driver)
        if "wings" in obj.name.lower():
            set_color(obj, hex_to_blender_rgb(hex_color))
        if "steering" in obj.name.lower():
            # we want to set this invisible for now
            obj.hide_viewport = True
            obj.hide_render = True

    bpy.ops.object.camera_add()
    camera = bpy.context.object
    camera.name = driver.title() + "_Camera"
    camera.location = (
        0,
        3.8,
        1.25,
    )  # Position the camera 5 units above the empty object
    camera.data.dof.focus_distance = 15
    camera.parent = empty_obj
    camera.rotation_euler = (
        math.radians(82),
        0,
        math.radians(180),
    )  # Rotate 90 degrees around Z-axis

    for col in camera.users_collection:
        col.objects.unlink(camera)
    # Link only to driver collection
    driver_collection.objects.link(camera)

    return new_empty, wheels_objs


# Time,X,Y,Z,RotW,RotX,RotY,RotZ
def add_keyframes(driver_obj, wheels_objs, df):
    for i in range(len(df)):
        idx = i + 1

        # point = mathutils.Vector((df["X"][i], df["Y"][i], df["Z"][i]))
        # TODO: for now setting all z to 0 because cars appear to be under the track
        point = mathutils.Vector((df["X"][i], df["Y"][i], 0))

        rot_eul = mathutils.Quaternion((
            df["RotW"][i],
            df["RotX"][i],
            df["RotY"][i],
            df["RotZ"][i],
        )).to_euler()
        harsher_rot_eul = mathutils.Quaternion((
            df["HarsherRotW"][i],
            df["HarsherRotX"][i],
            df["HarsherRotY"][i],
            df["HarsherRotZ"][i],
        )).to_euler()

        # for the front wheels, get the differences between the z's for harsher and normal, then add the diff to the front wheel rot
        front_wheel_diff = harsher_rot_eul[2] - rot_eul[2]

        wheel_rot = df["TireRot"][i]
        for wheel_obj in wheels_objs:
            # the other infos for y, z may change so just grab what already exists first
            rot = wheel_obj.rotation_euler
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


def main(driver_dfs, drivers, driver_colors, is_quick_validate_mode):
    empty_obj, base_collection = load_base_car_fbx()

    driver_objs = {}
    for i, driver_abbrev in enumerate(drivers):
        if is_quick_validate_mode and i >= 2:
            continue

        log_info(
            f"Adding driver {i + 1}/{len(drivers)}: {driver_abbrev} with color: {
                driver_colors[i]
            }"
        )
        driver_obj, wheels_objs = create_driver_fbx(
            driver_abbrev, driver_colors[i], empty_obj
        )
        add_keyframes(driver_obj, wheels_objs, driver_dfs[driver_abbrev])

        driver_objs[driver_abbrev] = driver_obj

    bpy.data.collections.remove(base_collection, do_unlink=True)

    return driver_objs
