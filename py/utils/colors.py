def hex_to_blender_rgb(hex_color: str) -> tuple:
    # Convert a hex color to a Blender RGB tuple.
    # In blender, the RGB values are between 0 and 1.
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i : i + 2], 16) / 255 for i in (0, 2, 4))


def hex_to_normal_rgb(hex_color: str) -> tuple:
    # Convert a hex color to a normal RGB tuple.
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))
