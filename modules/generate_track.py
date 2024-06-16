from io import StringIO

import bmesh
import bpy
import pandas as pd
import requests


def _create_planes(inner_points, outer_points, name, material):
    mesh = bpy.data.meshes.new(name + "TrackMesh")
    obj = bpy.data.objects.new(name + "Track", mesh)
    bpy.context.collection.objects.link(obj)

    bm = bmesh.new()

    inner_verts = [bm.verts.new(coord) for coord in inner_points]
    outer_verts = [bm.verts.new(coord) for coord in outer_points]

    bm.verts.ensure_lookup_table()

    for i in range(len(inner_points) - 1):
        bm.faces.new([inner_verts[i], inner_verts[i + 1], outer_verts[i + 1], outer_verts[i]])
    # bm.faces.new([inner_verts[-1], inner_verts[0], outer_verts[0], outer_verts[-1]])

    bm.to_mesh(mesh)
    bm.free()

    if material:
        obj.data.materials.append(material)


def _create_material(hex_color, name):
    # Convert hex to RGB
    hex_color = hex_color.lstrip("#")
    rgb = tuple(int(hex_color[i : i + 2], 16) / 255.0 for i in (0, 2, 4))

    # Create the material
    mat = bpy.data.materials.new(name=name + "TrackMaterial")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*rgb, 1)

    return mat


def _import_data(year, track):
    folder_loc = f"https://raw.githubusercontent.com/formula-viz/track-data-process/main/track_data/{year}_{track}.csv"

    # when we fetch we need a username and password with requests
    response = requests.get(folder_loc, auth=("quinn-caverly", "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"))

    data = StringIO(response.text)
    df = pd.read_csv(data, header=0)

    return df


def generate_track(year, track, main_track_color, curb_color):
    track_collection = bpy.data.collections.new(name="TrackCollection")
    bpy.context.scene.collection.children.link(track_collection)
    bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children[-1]

    track_mat = _create_material(main_track_color, "Main")
    curb_mat = _create_material(curb_color, "Curb")

    df = _import_data(year, track)

    inner_points = df[["inner_X", "inner_Y", "inner_Z"]].values.tolist()
    outer_points = df[["outer_X", "outer_Y", "outer_Z"]].values.tolist()

    inner_curb_points = df[["inner_curb_X", "inner_curb_Y", "inner_curb_Z"]].values.tolist()
    outer_curb_points = df[["outer_curb_X", "outer_curb_Y", "outer_curb_Z"]].values.tolist()

    _create_planes(inner_points, outer_points, "Main", track_mat)
    _create_planes(outer_points, outer_curb_points, "CurbOuter", curb_mat)
    _create_planes(inner_points, inner_curb_points, "CurbInner", curb_mat)
