import math

import bmesh
import bpy
from utils.colors import hex_to_blender_rgb


def add_start_finish_line(inner_points, outer_points, car_df, at_start):
    # the car passes the start/finish line at the at_start frame
    # we want to find the points in inner_point and outer_point closest to the start/finish add_start_finish_line
    # then, we add a plane that goes from the inner point to the outer point
    basis_point = car_df.iloc[at_start][["X", "Y", "Z"]].values.tolist()

    closest_inner = (math.inf, math.inf, math.inf)
    closest_inner_idx = -1
    closest_outer = (math.inf, math.inf, math.inf)
    closest_outer_idx = -1

    for idx, (inner, outer) in enumerate(zip(inner_points, outer_points)):
        inner_dist = math.dist(inner, basis_point)
        outer_dist = math.dist(outer, basis_point)

        if inner_dist < math.dist(closest_inner, basis_point):
            closest_inner = inner
            closest_inner_idx = idx
        if outer_dist < math.dist(closest_outer, basis_point):
            closest_outer = outer
            closest_outer_idx = idx

    # because the important line is the leading edge, or the line closest to the car,
    # if we want the line to have some width we will move away from the closest_inner and closest_outer

    # we want to build a plane with several vertices
    line_width = 3  # width in points

    points = []
    for i in range(0, line_width):
        points.append(inner_points[(closest_inner_idx - i) % len(inner_points)])

    # add the others in reverse order so that the plane is built correctly
    for i in reversed(range(0, line_width)):
        points.append(outer_points[(closest_outer_idx - i) % len(outer_points)])

    # we want to add a tiny bit of height to the line so that it does not conflict with the main track
    for i in range(len(points)):
        points[i] = (points[i][0], points[i][1], points[i][2] + 0.02)

    mesh = bpy.data.meshes.new("StartFinishLineMesh")
    obj = bpy.data.objects.new("StartFinishLine", mesh)
    bpy.context.collection.objects.link(obj)

    bm = bmesh.new()
    for point in points:
        bm.verts.new(point)

    bm.verts.ensure_lookup_table()
    bm.faces.new(bm.verts)
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()

    mat = bpy.data.materials.new(name="StartFinishLineMaterial")
    mat.use_nodes = True

    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (0.01, 0.01, 0.01, 1)

    obj.data.materials.append(mat)


# where at_start is the index of the point where the car is at the start/finish line
def main(inner_points, outer_points, inner_curb_points, outer_curb_points, car_df, at_start=0):
    add_start_finish_line(inner_curb_points, outer_curb_points, car_df, at_start)
