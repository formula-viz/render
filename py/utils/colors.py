import numpy as np
from colormath.color_conversions import convert_color
from colormath.color_diff import delta_e_cie2000
from colormath.color_objects import LabColor, sRGBColor
from fastf1 import plotting

GOLD_RGB = (255, 215, 0)
MAIN_TRACK_COLOR = "#2d2e2e"
CURB_COLOR = "#0f0f0f"
SCENE_BG_COLOR = "#171717"


def hex_to_blender_rgb(hex_color: str) -> tuple:
    # Convert a hex color to a Blender RGB tuple.
    # In blender, the RGB values are between 0 and 1.
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i : i + 2], 16) / 255.0 for i in (0, 2, 4))


def hex_to_normal_rgb(hex_color: str) -> tuple:
    # Convert a hex color to a normal RGB tuple.
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))


def rgb_to_hex(rgb_color: tuple) -> str:
    # Convert an RGB tuple to a hex color.
    return f"#{''.join(f'{int(x):02x}' for x in rgb_color)}"


# 19 gray scale colors and one gold color, the gold must be at index 0
def get_rest_of_field_colors():
    gray_scale = [(x, x, x) for x in np.linspace(70, 255, 19, dtype=float)]
    gray_scale.insert(0, GOLD_RGB)

    return [rgb_to_hex(x) for x in gray_scale]


def get_head_to_head_colors(*drivers):
    def rgb_to_lab(rgb):
        srgb = sRGBColor(*rgb, is_upscaled=True)
        return convert_color(srgb, LabColor)

    def color_difference(hex1, hex2):
        rgb1 = hex_to_normal_rgb(hex1)
        rgb2 = hex_to_normal_rgb(hex2)

        lab1 = rgb_to_lab(rgb1)
        lab2 = rgb_to_lab(rgb2)

        # this code fixed asscalar deprecation used by colormath
        def patch_asscalar(a):
            return a.item()

        setattr(np, "asscalar", patch_asscalar)
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


def blender_rgb_to_linear(tup):
    def srgb_to_linearrgb(c):
        if c < 0:
            return 0
        elif c < 0.04045:
            return c / 12.92
        else:
            return ((c + 0.055) / 1.055) ** 2.4

    return tuple(srgb_to_linearrgb(x) for x in tup)


class CurbColor:
    @staticmethod
    def get_scene_rgb():
        return blender_rgb_to_linear(hex_to_blender_rgb(CURB_COLOR))


class MainTrackColor:
    @staticmethod
    def get_scene_rgb():
        return blender_rgb_to_linear(hex_to_blender_rgb(MAIN_TRACK_COLOR))


class StartFinishLineColor:
    @staticmethod
    def get_scene_rgb():
        return blender_rgb_to_linear(hex_to_blender_rgb(CURB_COLOR))


class BackgroundColor:
    @staticmethod
    def get_scene_rgb():
        return blender_rgb_to_linear(hex_to_blender_rgb(SCENE_BG_COLOR))

    @staticmethod
    def get_sequence_editor_rgb():
        return hex_to_blender_rgb(SCENE_BG_COLOR)
