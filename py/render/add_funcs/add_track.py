"""Generate track surfaces and curbs with appropriate materials."""

import bmesh
import bpy

from py.utils.colors import CurbColor, MainTrackColor


def create_planes(inner_points, outer_points, name, material=None):
    """Create a mesh plane between two sets of points.

    Args:
        inner_points: List of 3D coordinates representing the inner edge
        outer_points: List of 3D coordinates representing the outer edge
        name: Base name for the created object
        material: Blender material to apply to the mesh (optional)

    Returns:
        The created Blender object

    """
    mesh = bpy.data.meshes.new(name + "TrackMesh")
    obj = bpy.data.objects.new(name + "Track", mesh)
    bpy.context.collection.objects.link(obj)  # pyright: ignore

    bm = bmesh.new()

    inner_verts = [bm.verts.new(coord) for coord in inner_points]
    outer_verts = [bm.verts.new(coord) for coord in outer_points]

    bm.verts.ensure_lookup_table()

    for i in range(len(inner_points) - 1):
        bm.faces.new(
            [inner_verts[i], inner_verts[i + 1], outer_verts[i + 1], outer_verts[i]]
        )
    if len(inner_points) > 2:
        bm.faces.new([inner_verts[-1], inner_verts[0], outer_verts[0], outer_verts[-1]])

    bm.to_mesh(mesh)
    bm.free()

    if material:
        obj.data.materials.append(material)  # pyright: ignore

    return obj


def create_material(color, name):
    """Create a Blender material with the specified color.

    Args:
        color: RGB color values as a tuple (r, g, b)
        name: Base name for the material

    Returns:
        The created Blender material

    """
    mat = bpy.data.materials.new(name=name + "TrackMaterial")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]  # pyright: ignore
    bsdf.inputs["Base Color"].default_value = (*color, 1)  # pyright: ignore
    return mat


def main(track_data):
    """Create the complete track with main surfaces and curbs.

    Args:
        track_data: Object containing track point data with the following properties:
                   - inner_points: List of 3D coordinates for inner track edge
                   - outer_points: List of 3D coordinates for outer track edge
                   - inner_curb_points: List of 3D coordinates for inner curb edge
                   - outer_curb_points: List of 3D coordinates for outer curb edge

    """
    track_collection = bpy.data.collections.new(name="TrackCollection")
    bpy.context.scene.collection.children.link(track_collection)  # pyright: ignore
    bpy.context.view_layer.active_layer_collection = (  # pyright: ignore
        bpy.context.view_layer.layer_collection.children[-1]  # pyright: ignore
    )

    track_mat = create_material(MainTrackColor.get_scene_rgb(), "Main")
    curb_mat = create_material(CurbColor.get_scene_rgb(), "Curb")

    create_planes(track_data.inner_points, track_data.outer_points, "Main", track_mat)
    create_planes(
        track_data.outer_points, track_data.outer_curb_points, "CurbOuter", curb_mat
    )
    create_planes(
        track_data.inner_points, track_data.inner_curb_points, "CurbInner", curb_mat
    )
