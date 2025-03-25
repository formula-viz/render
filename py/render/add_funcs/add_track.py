"""Generate track surfaces and curbs with appropriate materials."""

import math
from typing import Optional

import bmesh
import bpy

from py.utils.colors import MainTrackColor
from py.utils.materials import create_magic_material
from py.utils.models import AppState, SectorsInfo


def create_boxes(
    inner_points: list[tuple[float, float, float]],
    outer_points: list[tuple[float, float, float]],
    sectors_info: SectorsInfo,
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
        bottom_face = bm.faces.new(
            [
                bottom_inner_verts[i],
                bottom_inner_verts[i + 1],
                bottom_outer_verts[i + 1],
                bottom_outer_verts[i],
            ]
        )
        all_faces.append(bottom_face)

        # Top face
        top_face = bm.faces.new(
            [
                top_inner_verts[i],
                top_inner_verts[i + 1],
                top_outer_verts[i + 1],
                top_outer_verts[i],
            ]
        )
        all_faces.append(top_face)

        # Inner side face
        inner_side_face = bm.faces.new(
            [
                bottom_inner_verts[i],
                bottom_inner_verts[i + 1],
                top_inner_verts[i + 1],
                top_inner_verts[i],
            ]
        )
        all_faces.append(inner_side_face)

        # Outer side face
        outer_side_face = bm.faces.new(
            [
                bottom_outer_verts[i],
                bottom_outer_verts[i + 1],
                top_outer_verts[i + 1],
                top_outer_verts[i],
            ]
        )
        all_faces.append(outer_side_face)

        # Start cap face (only for the first segment)
        if i == 0:
            start_cap_face = bm.faces.new(
                [
                    bottom_inner_verts[0],
                    bottom_outer_verts[0],
                    top_outer_verts[0],
                    top_inner_verts[0],
                ]
            )
            all_faces.append(start_cap_face)

        # End cap face (for each segment end)
        end_cap_face = bm.faces.new(
            [
                bottom_inner_verts[i + 1],
                bottom_outer_verts[i + 1],
                top_outer_verts[i + 1],
                top_inner_verts[i + 1],
            ]
        )
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


def create_planes_curb(
    inner_points: list[tuple[float, float, float]],
    outer_points: list[tuple[float, float, float]],
    name: str,
    default_material: bpy.types.Material,
    curbstone_a_mat: bpy.types.Material,
    curbstone_b_mat: bpy.types.Material,
    curve_threshold: float = 0.07,
):
    """Create a mesh plane with curb patterns only on curved sections.

    Args:
        inner_points: List of 3D coordinates representing the inner edge
        outer_points: List of 3D coordinates representing the outer edge
        name: Base name for the created object
        material: Blender material for the main curb surface
        alternate_material: Blender material for the curb pattern
        curve_threshold: Minimum angle (in radians) to consider a section as curved

    Returns:
        The created Blender object

    """
    mesh = bpy.data.meshes.new(name + "CurbMesh")
    obj = bpy.data.objects.new(name + "Curb", mesh)
    bpy.context.collection.objects.link(obj)  # pyright: ignore

    bm = bmesh.new()

    # Create all vertices for inner and outer edges
    inner_verts = [bm.verts.new(coord) for coord in inner_points]
    outer_verts = [bm.verts.new(coord) for coord in outer_points]

    bm.verts.ensure_lookup_table()  # pyright: ignore

    # List to track which segments are curved
    is_curved_segment = []

    # Create faces and determine if each segment is curved
    faces = []
    for i in range(len(inner_points) - 1):
        # Create the face
        face = bm.faces.new(
            [inner_verts[i], inner_verts[i + 1], outer_verts[i + 1], outer_verts[i]]
        )
        faces.append(face)

        # Determine if this segment is part of a curve
        # Calculate angle between consecutive segments
        is_curved = False

        if i > 0 and i < len(inner_points) - 3:
            # Use wider spacing for better curve detection
            skip_distance = 20
            prev_idx = max(0, i - skip_distance)
            next_idx = min(len(inner_points) - 1, i + skip_distance)

            prev_point = inner_points[prev_idx]
            cur_point = inner_points[i]
            next_point = inner_points[next_idx]

            # Get vectors between these more distant points
            prev_vec = (
                cur_point[0] - prev_point[0],
                cur_point[1] - prev_point[1],
            )
            curr_vec = (
                next_point[0] - cur_point[0],
                next_point[1] - cur_point[1],
            )

            # Calculate angle using dot product
            dot_product = prev_vec[0] * curr_vec[0] + prev_vec[1] * curr_vec[1]
            prev_len = (prev_vec[0] ** 2 + prev_vec[1] ** 2) ** 0.5
            curr_len = (curr_vec[0] ** 2 + curr_vec[1] ** 2) ** 0.5

            if prev_len > 0 and curr_len > 0:
                cos_angle = dot_product / (prev_len * curr_len)
                # Clamp to avoid numerical errors
                cos_angle = max(min(cos_angle, 1.0), -1.0)
                angle = abs(math.acos(cos_angle))

                # If angle is greater than threshold, it's a curve
                is_curved = angle > curve_threshold
        is_curved_segment.append(is_curved)

    # Apply the mesh to the object
    bm.to_mesh(mesh)  # pyright: ignore
    bm.free()  # pyright: ignore

    # Add materials
    obj.data.materials.append(default_material)  # pyright: ignore
    obj.data.materials.append(curbstone_a_mat)  # pyright: ignore
    obj.data.materials.append(curbstone_b_mat)  # pyright: ignore

    # Variables to track the state of curb pattern
    in_curve = False
    current_material = 1  # Start with curbstone_a_mat (index 1)
    accumulated_area = 0.0
    target_area = 4.0  # 4 square meters per pattern segment

    # Assign material indices to faces
    for i, poly in enumerate(obj.data.polygons):  # pyright: ignore
        # Calculate face area (approximate)
        face_area = poly.area

        # If we're entering a curve
        if is_curved_segment[i] and not in_curve:
            in_curve = True
            accumulated_area = 0.0
            current_material = 1  # Start with curbstone_a_mat

        # If we're in a curve or completing a pattern segment
        if in_curve:
            # Assign current material
            poly.material_index = current_material

            # Add face area to accumulated area
            accumulated_area += face_area

            # Check if we've completed a pattern segment
            if accumulated_area >= target_area:
                # Switch materials
                current_material = 3 - current_material  # Toggle between 1 and 2
                accumulated_area = 0.0  # Reset accumulated area

                # If we've left the curve, check if any of the next 10 elements are curved
                if not is_curved_segment[i]:
                    # Look ahead to see if we should stay in curve mode
                    stay_in_curve = False
                    for j in range(1, 21):  # Check next 20 segments
                        look_ahead_idx = (i + j) % len(is_curved_segment)
                        if is_curved_segment[look_ahead_idx]:
                            stay_in_curve = True
                            break
                    in_curve = stay_in_curve
        else:
            # Not in curve, use default material
            poly.material_index = 0
    return obj


def create_planes(
    inner_points: list[tuple[float, float, float]],
    outer_points: list[tuple[float, float, float]],
    name: str,
    material: Optional[bpy.types.Material] = None,
    alternate_material: Optional[bpy.types.Material] = None,
    is_curb: bool = True,
):
    """Create a mesh plane between two sets of points.

    Args:
        inner_points: List of 4D coordinates representing the inner edge
        outer_points: List of 4D coordinates representing the outer edge
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

    bm.to_mesh(mesh)  # pyright: ignore
    bm.free()  # pyright: ignore

    pattern_size = 5
    if material:
        obj.data.materials.append(material)  # pyright: ignore

        # Create alternating pattern for curbs
        if is_curb and alternate_material:
            obj.data.materials.append(alternate_material)  # pyright: ignore

            # Assign material indices to faces
            for i, poly in enumerate(obj.data.polygons):  # pyright: ignore
                # Integer division to determine which material to use
                # e.g., with pattern_size=4: 0,1,2 get mat1, 3,4,5 get mat2, etc.
                material_index = (i // pattern_size) % 3
                poly.material_index = material_index

    return obj


def create_material(
    color: tuple[float, float, float], name: str, emission_value: float = 0.0
):
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


def main(state: AppState) -> None:
    """Create the complete track with main surfaces and curbs.

    Args:
        state: The application state containing track data.

    """
    track_collection = bpy.data.collections.new(name="TrackCollection")
    bpy.context.scene.collection.children.link(track_collection)  # pyright: ignore
    bpy.context.view_layer.active_layer_collection = (  # pyright: ignore
        bpy.context.view_layer.layer_collection.children[-1]  # pyright: ignore
    )

    track_mat = create_material(MainTrackColor.get_scene_rgb(), "Main", 0.5)
    curb_mat = create_material((0, 0, 0), "Curb")
    curbstone_a_mat = create_magic_material((1, 1, 1), "CurbstoneA")
    # curbstone_a_mat = create_material((1, 1, 1), "CurbstoneA")
    curbstone_b_mat = create_material((0.128, 0, 0), "CurbstoneB")

    line_mat = create_material((0.5, 0.5, 0.5), "Line", 0.1)

    assert state.track_data is not None
    create_planes(
        state.track_data.inner_points, state.track_data.outer_points, "Main", track_mat
    )

    create_planes_curb(
        state.track_data.outer_points,
        state.track_data.outer_curb_points,
        "CurbOuter",
        curb_mat,
        curbstone_a_mat,
        curbstone_b_mat,
    )
    create_planes_curb(
        state.track_data.inner_points,
        state.track_data.inner_curb_points,
        "CurbInner",
        curb_mat,
        curbstone_a_mat,
        curbstone_b_mat,
    )

    assert state.sectors_info is not None
    if state.track_data.inner_trace_line and state.track_data.outer_trace_line:
        create_boxes(
            state.track_data.inner_trace_line.a_points,
            state.track_data.inner_trace_line.b_points,
            state.sectors_info,
            "InnerLine",
            0.005,
            line_mat,
        )
        create_boxes(
            state.track_data.outer_trace_line.a_points,
            state.track_data.outer_trace_line.b_points,
            state.sectors_info,
            "OuterLine",
            0.005,
            line_mat,
        )
