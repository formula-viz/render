from colormath.color_conversions import convert_color
from colormath.color_diff import delta_e_cie2000
from colormath.color_objects import LabColor, sRGBColor
from fastf1 import plotting
import numpy


def hex_to_blender_rgb(hex_color: str) -> tuple:
    # Convert a hex color to a Blender RGB tuple.
    # In blender, the RGB values are between 0 and 1.
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i : i + 2], 16) / 255 for i in (0, 2, 4))


def hex_to_normal_rgb(hex_color: str) -> tuple:
    # Convert a hex color to a normal RGB tuple.
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))


def get_driver_colors(*drivers):
    def hex_to_rgb(hex_color):
        return tuple(int(hex_color[i : i + 2], 16) for i in (1, 3, 5))

    def rgb_to_lab(rgb):
        srgb = sRGBColor(*rgb, is_upscaled=True)
        return convert_color(srgb, LabColor)

    def color_difference(hex1, hex2):
        rgb1 = hex_to_rgb(hex1)
        rgb2 = hex_to_rgb(hex2)

        lab1 = rgb_to_lab(rgb1)
        lab2 = rgb_to_lab(rgb2)

        # this code fixed asscalar deprecation used by colormath
        def patch_asscalar(a):
            return a.item()

        setattr(numpy, "asscalar", patch_asscalar)
        delta_e = delta_e_cie2000(lab1, lab2)

        return delta_e

    base_colors = ["#FFFFFF", "#808080", "#404040"]  # white, gray, dark gray
    base_color_idx = 0

    colors = [plotting.DRIVER_COLORS[plotting.DRIVER_TRANSLATE[driver]] for driver in drivers]

    # reverse here because the first driver will be the one who won by convention, so
    # winning driver should keep their base color
    for i in reversed(range(1, len(colors))):
        if color_difference(colors[0], colors[i]) <= 30:
            colors[i] = base_colors[base_color_idx % len(base_colors)]
            base_color_idx += 1
            if color_difference(colors[0], colors[i]) <= 30:
                print(
                    f"Colors for driver {drivers[0]} and {drivers[i]} are too similar even after setting one to white, inspect this."
                )

            if base_color_idx >= len(base_colors):
                print("Ran out of base colors, investigate this.")

    return colors
