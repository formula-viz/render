import bmesh # pyright: ignore
import bpy # pyright: ignore
from add_track import create_material
from utils.colors import StartFinishLineColor


# we have gotten the index of the inner_points, outer_points defining the start/finish line
# from a previous function, so we just use that index here
def add_start_finish_line(inner_points, outer_points, start_finish_line_idx, prefix="StartFinishLine", line_width=3, z_offset=0.02):
    # we want to build a plane with several vertices
    # line_width is how many vertices we want to add to the line, usually this is about 2,000, 3 works well for normal track
    # for the status track, we will want to use a higher value, maybe 10

    points = []
    for i in range(0, line_width):
        points.append(inner_points[(start_finish_line_idx - i) % len(inner_points)])

    # add the others in reverse order so that the plane is built correctly
    for i in reversed(range(0, line_width)):
        points.append(outer_points[(start_finish_line_idx - i) % len(outer_points)])

    # we want to add a tiny bit of height to the line so that it does not conflict with the main track
    for i in range(len(points)):
        points[i] = (points[i][0], points[i][1], points[i][2] + z_offset)

    mesh = bpy.data.meshes.new(f"{prefix}Mesh")
    obj = bpy.data.objects.new(prefix, mesh)
    bpy.context.collection.objects.link(obj)

    bm = bmesh.new()
    for point in points:
        bm.verts.new(point)

    bm.verts.ensure_lookup_table()
    bm.faces.new(bm.verts)
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()

    mat = create_material(StartFinishLineColor.get_scene_rgb(), "StartFinishLineMaterial")

    obj.data.materials.append(mat)
    return obj


# where at_start is the index of the point where the car is at the start/finish line
def main(inner_curb_points, outer_curb_points, start_finish_line_idx):
    indicators_collection = bpy.data.collections.new(name="IndicatorsCollection")
    bpy.context.scene.collection.children.link(indicators_collection)
    bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children[-1]

    return add_start_finish_line(inner_curb_points, outer_curb_points, start_finish_line_idx)
