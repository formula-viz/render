import bpy


def configure_sun():
    sun_collection = bpy.data.collections.new(name="SunCollection")
    bpy.context.scene.collection.children.link(sun_collection)
    bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children[-1]

    light_data = bpy.data.lights.new(name="Sun-Data", type="SUN")
    light_data.energy = 5.0
    light_object = bpy.data.objects.new(name="Sun", object_data=light_data)

    bpy.context.collection.objects.link(light_object)
    light_object.location = (1000, 1000, 1000)
