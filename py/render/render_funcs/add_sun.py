import bpy


def main():
    sun_collection = bpy.data.collections.new(name="SunCollection")
    bpy.context.scene.collection.children.link(sun_collection)
    bpy.context.view_layer.active_layer_collection = (
        bpy.context.view_layer.layer_collection.children[-1]
    )

    light_data = bpy.data.lights.new(name="Sun-Data", type="SUN")
    light_data.energy = 2.5
    light_object = bpy.data.objects.new(name="Sun", object_data=light_data)

    # Add slight warm color to the sun (orange/golden tint)
    light_data.color = (1, 0.975, 0.9)  # RGB values for warm sunlight

    bpy.context.collection.objects.link(light_object)
    light_object.location = (1000, 1000, 1000)
