import os
import sys

script_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(script_path)

from modules.configure_sun import configure_sun
from modules.delete_default_collection import delete_default_collection
from modules.generate_track import generate_track

if __name__ == "__main__":
    year = 2023
    track = "CAN"

    delete_default_collection()
    configure_sun()
    generate_track(year, track, "#605B56", "#837a75")
