import bmesh
import bpy
import pandas as pd
from utils.project_structure import get_track_data_path


def create_planes(inner_points, outer_points, name, material=None):
    mesh = bpy.data.meshes.new(name + "TrackMesh")
    obj = bpy.data.objects.new(name + "Track", mesh)
    bpy.context.collection.objects.link(obj)

    bm = bmesh.new()

    inner_verts = [bm.verts.new(coord) for coord in inner_points]
    outer_verts = [bm.verts.new(coord) for coord in outer_points]

    bm.verts.ensure_lookup_table()

    for i in range(len(inner_points) - 1):
        bm.faces.new([inner_verts[i], inner_verts[i + 1], outer_verts[i + 1], outer_verts[i]])
    bm.faces.new([inner_verts[-1], inner_verts[0], outer_verts[0], outer_verts[-1]])

    bm.to_mesh(mesh)
    bm.free()

    if material:
        obj.data.materials.append(material)


def create_material(color, name):
    mat = bpy.data.materials.new(name=name + "TrackMaterial")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*color, 1)

    return mat


def main(inner_points, outer_points, inner_curb_points, outer_curb_points):
    track_collection = bpy.data.collections.new(name="TrackCollection")
    bpy.context.scene.collection.children.link(track_collection)
    bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children[-1]

    dark_gray = (0.02, 0.02, 0.02)
    darker_gray = (0.01, 0.01, 0.01)
    track_mat = create_material(dark_gray, "Main")
    curb_mat = create_material(darker_gray, "Curb")

    create_planes(inner_points, outer_points, "Main", track_mat)
    create_planes(outer_points, outer_curb_points, "CurbOuter", curb_mat)
    create_planes(inner_points, inner_curb_points, "CurbInner", curb_mat)

    return inner_points, outer_points, inner_curb_points, outer_curb_points
