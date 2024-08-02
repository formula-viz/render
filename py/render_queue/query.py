import logging
import os
import sys

import fastf1 as ff1
import yaml
from colormath.color_conversions import convert_color
from colormath.color_diff import delta_e_cie2000
from colormath.color_objects import LabColor, sRGBColor
from fastf1 import plotting

# add project root directory to the system path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.project_structure import CUR_YEAR, STAGING_DIR, TRACKS_FILE


def general_write_yaml(track: str, year: int, drivers: list):
    data = {
        "track": track,
        "year": year,
        "render": {
            "should_render": True,
            "validate_render": False,
            "fps": 30,
            "samples": 4096,
            "adaptive_sampling": True,
            "is_4k": True,
            "output": "output.mp4",
        },
        "drivers": drivers,
    }

    # uniquely identify by the year, track, driver names
    yaml_name = f"{year}_{track}_{'_'.join([driver['name'] for driver in drivers])}.yaml"
    yaml_path = os.path.join(STAGING_DIR, yaml_name)

    with open(yaml_path, "w") as file:
        yaml.safe_dump(data, file, default_flow_style=False, sort_keys=False)


def get_top_two_drivers(year: int, track: str):
    session = ff1.get_session(year, track, "Q")
    session.load()

    results = session.results

    # Sort the results by position and get the top two
    top_two = results.sort_values("Position")[:2]

    # Extract the driver codes for the top two
    pole_position = top_two.iloc[0]
    second_place = top_two.iloc[1]

    return pole_position["Abbreviation"], second_place["Abbreviation"]


def get_colors(pole, second):
    pole_color = plotting.DRIVER_COLORS[plotting.DRIVER_TRANSLATE[pole]]
    second_color = plotting.DRIVER_COLORS[plotting.DRIVER_TRANSLATE[second]]

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
        import numpy

        def patch_asscalar(a):
            return a.item()

        setattr(numpy, "asscalar", patch_asscalar)

        delta_e = delta_e_cie2000(lab1, lab2)

        return delta_e

    dif = color_difference(pole_color, second_color)
    if dif <= 15:  # if they are too similar, set the second to white
        second_color = "#FFFFFF"
        # there is a small chance that they are still too similar
        new_dif = color_difference(pole_color, second_color)
        if new_dif <= 15:
            logging.warning("Colors are too similar even after setting one to white, inspect this.")

        if new_dif > dif:
            _, second_color = get_colors(pole, second)

    return pole_color, second_color


def load_tracks():
    if not os.path.exists(TRACKS_FILE):
        return []
    with open(TRACKS_FILE, "r") as file:
        return [line.strip() for line in file if line.strip()]


def save_tracks(tracks):
    with open(TRACKS_FILE, "w") as file:
        for track in tracks:
            file.write(f"{track}\n")


def check_api_data(year, track):
    try:
        session = ff1.get_session(year, track, "Q")
        session.load()

        # TODO: this should ensure that the data exists, or split qualis will fail
        session.laps.split_qualifying_sessions()
        return True
    except:
        return False


def main():
    tracks = load_tracks()
    # realistically, only one will ever be removed at a time, but I am implementing
    # like this so I won't need to consider which side is top / bottom
    uncomplete = []
    for track in tracks:
        if not check_api_data(CUR_YEAR, track):
            uncomplete.append(track)
        else:
            # when the data is ready, we head off the entire process, by placing in queue
            pole, second = get_top_two_drivers(CUR_YEAR, track)
            pole_color, second_color = get_colors(pole, second)

            drivers = [{"name": pole, "pos": 1, "color": pole_color}, {"name": second, "pos": 2, "color": second_color}]
            general_write_yaml(track, CUR_YEAR, drivers)

    save_tracks(uncomplete)


main()
