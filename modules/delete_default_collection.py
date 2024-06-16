import bpy

def delete_default_collection():
    bpy.data.collections.remove(bpy.data.collections["Collection"], do_unlink=True)
