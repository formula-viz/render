import bmesh
import bpy


# we have gotten the index of the inner_points, outer_points defining the start/finish line
# from a previous function, so we just use that index here
def add_start_finish_line(inner_points, outer_points, start_finish_line_idx):
    # we want to build a plane with several vertices
    line_width = 3  # width in points

    points = []
    for i in range(0, line_width):
        points.append(inner_points[(start_finish_line_idx - i) % len(inner_points)])

    # add the others in reverse order so that the plane is built correctly
    for i in reversed(range(0, line_width)):
        points.append(outer_points[(start_finish_line_idx - i) % len(outer_points)])

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
    bsdf.inputs["Base Color"].default_value = (0.38, 0.38, 0.38, 1)

    obj.data.materials.append(mat)


# where at_start is the index of the point where the car is at the start/finish line
def main(inner_curb_points, outer_curb_points, start_finish_line_idx):
    indicators_collection = bpy.data.collections.new(name="IndicatorsCollection")
    bpy.context.scene.collection.children.link(indicators_collection)
    bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children[-1]

    add_start_finish_line(inner_curb_points, outer_curb_points, start_finish_line_idx)
