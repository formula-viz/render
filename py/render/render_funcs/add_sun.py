"""Add a sun to the scene."""

import bpy


def main():
    """Add a sun to the scene."""
    sun_collection = bpy.data.collections.new(name="SunCollection")
    bpy.context.scene.collection.children.link(sun_collection)  # pyright: ignore
    bpy.context.view_layer.active_layer_collection = (  # pyright: ignore
        bpy.context.view_layer.layer_collection.children[-1]  # pyright: ignore
    )

    light_data = bpy.data.lights.new(name="Sun-Data", type="SUN")
    light_data.energy = 2.5  # pyright: ignore
    light_object = bpy.data.objects.new(name="Sun", object_data=light_data)

    # Add slight warm color to the sun (orange/golden tint)
    light_data.color = (1, 0.9875, 0.95)  # RGB values for warm sunlight

    bpy.context.collection.objects.link(light_object)  # pyright: ignore
    light_object.location = (1000, 1000, 1000)
