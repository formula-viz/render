import bpy

def set_background_color():
    bpy.context.scene.world.node_tree.nodes["Background"].inputs[0].default_value = (0.6, 0.6, 0.6, 1)
