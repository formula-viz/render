"""Generate track surfaces and curbs with appropriate materials."""

from typing import Optional

import bmesh
import bpy

from py.render.data_funcs.load_track_data import TrackData
from py.utils.colors import CurbColor, MainTrackColor


def create_boxes(
    inner_points: list[tuple[float, float, float]],
    outer_points: list[tuple[float, float, float]],
    name: str,
    height: float = 0.1,
    material: Optional[bpy.types.Material] = None,
    alternate_material: Optional[bpy.types.Material] = None,
    is_pattern: bool = False,
):
    """Create a mesh of 3D boxes between two sets of points.

    Args:
        inner_points: List of 3D coordinates representing the inner edge
        outer_points: List of 3D coordinates representing the outer edge
        name: Base name for the created object
        height: Height of the boxes
        material: Blender material to apply to the mesh (optional)
        alternate_material: Second material for alternating pattern (optional)
        is_pattern: Whether to apply an alternating material pattern

    Returns:
        The created Blender object
    """
    mesh = bpy.data.meshes.new(name + "BoxMesh")
    obj = bpy.data.objects.new(name + "Box", mesh)
    bpy.context.collection.objects.link(obj)  # pyright: ignore

    bm = bmesh.new()

    # Create vertices for the bottom face
    bottom_inner_verts = [bm.verts.new(coord) for coord in inner_points]
    bottom_outer_verts = [bm.verts.new(coord) for coord in outer_points]

    # Create vertices for the top face (add height to z-coordinate)
    top_inner_verts = [bm.verts.new((p[0], p[1], p[2] + height)) for p in inner_points]
    top_outer_verts = [bm.verts.new((p[0], p[1], p[2] + height)) for p in outer_points]

    bm.verts.ensure_lookup_table()  # pyright: ignore

    # List to store all created faces
    all_faces = []

    # Create faces for each segment
    for i in range(len(inner_points) - 1):
        # Bottom face
        bottom_face = bm.faces.new([
            bottom_inner_verts[i], bottom_inner_verts[i + 1],
            bottom_outer_verts[i + 1], bottom_outer_verts[i]
        ])
        all_faces.append(bottom_face)

        # Top face
        top_face = bm.faces.new([
            top_inner_verts[i], top_inner_verts[i + 1],
            top_outer_verts[i + 1], top_outer_verts[i]
        ])
        all_faces.append(top_face)

        # Inner side face
        inner_side_face = bm.faces.new([
            bottom_inner_verts[i], bottom_inner_verts[i + 1],
            top_inner_verts[i + 1], top_inner_verts[i]
        ])
        all_faces.append(inner_side_face)

        # Outer side face
        outer_side_face = bm.faces.new([
            bottom_outer_verts[i], bottom_outer_verts[i + 1],
            top_outer_verts[i + 1], top_outer_verts[i]
        ])
        all_faces.append(outer_side_face)

        # Start cap face (only for the first segment)
        if i == 0:
            start_cap_face = bm.faces.new([
                bottom_inner_verts[0], bottom_outer_verts[0],
                top_outer_verts[0], top_inner_verts[0]
            ])
            all_faces.append(start_cap_face)

        # End cap face (for each segment end)
        end_cap_face = bm.faces.new([
            bottom_inner_verts[i + 1], bottom_outer_verts[i + 1],
            top_outer_verts[i + 1], top_inner_verts[i + 1]
        ])
        all_faces.append(end_cap_face)

    bm.to_mesh(mesh)  # pyright: ignore
    bm.free()  # pyright: ignore

    # Add materials
    if material:
        obj.data.materials.append(material)  # pyright: ignore

        # Create alternating pattern
        pattern_size = 6  # Number of faces per segment (6 faces per box)
        if is_pattern and alternate_material:
            obj.data.materials.append(alternate_material)  # pyright: ignore

            # Assign material indices to faces
            for i, poly in enumerate(obj.data.polygons):  # pyright: ignore
                # Integer division to determine which material to use
                # Each box has 6 faces, so divide by 6 to get box index
                segment_index = i // pattern_size
                material_index = segment_index % 2  # Alternate between 0 and 1
                poly.material_index = material_index

    return obj


def create_planes(
    inner_points: list[tuple[float, float, float]],
    outer_points: list[tuple[float, float, float]],
    name: str,
    material: Optional[bpy.types.Material] = None,
    alternate_material: Optional[bpy.types.Material] = None,
    is_curb: bool = False,
):
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

    bm.verts.ensure_lookup_table()  # pyright: ignore

    for i in range(len(inner_points) - 1):
        bm.faces.new(
            [inner_verts[i], inner_verts[i + 1], outer_verts[i + 1], outer_verts[i]]
        )
    # if len(inner_points) > 2:
    #     bm.faces.new([inner_verts[-1], inner_verts[0], outer_verts[0], outer_verts[-1]])

    bm.to_mesh(mesh)  # pyright: ignore
    bm.free()  # pyright: ignore

    pattern_size = 4
    if material:
        obj.data.materials.append(material)  # pyright: ignore

        # Create alternating pattern for curbs
        if is_curb and alternate_material:
            obj.data.materials.append(alternate_material)  # pyright: ignore

            # Assign material indices to faces
            for i, poly in enumerate(obj.data.polygons):  # pyright: ignore
                # Integer division to determine which material to use
                # e.g., with pattern_size=3: 0,1,2 get mat1, 3,4,5 get mat2, etc.
                material_index = (i // pattern_size) % 2
                poly.material_index = material_index

    return obj


def create_material(color: tuple[float, float, float], name: str, emission_value: float = 0.0):
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

    bsdf.inputs["Emission Color"].default_value = (*color, 1)  # pyright: ignore
    bsdf.inputs["Emission Strength"].default_value = emission_value  # pyright: ignore

    return mat


def main(track_data: TrackData) -> None:
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
    line_mat = create_material((0.6, 0.6, 0.6), "Line", 0.6)
    # alternate_curb_mat = create_material(AlternateCurbColor.get_scene_rgb(), "AlternateCurb")

    create_planes(track_data.inner_points, track_data.outer_points, "Main", track_mat)
    create_planes(
        track_data.outer_points, track_data.outer_curb_points, "CurbOuter", curb_mat
    )
    create_planes(
        track_data.inner_points, track_data.inner_curb_points, "CurbInner", curb_mat
    )

    if track_data.inner_trace_line and track_data.outer_trace_line:
        create_boxes(track_data.inner_trace_line.a_points, track_data.inner_trace_line.b_points, "InnerLine", 0.025, line_mat)
        create_boxes(track_data.outer_trace_line.a_points, track_data.outer_trace_line.b_points, "OuterLine", 0.025, line_mat)
