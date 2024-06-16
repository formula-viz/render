import sys
import os

script_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(script_path)

from modules.generate_track import generate_track

if __name__ == "__main__":
    year = 2023
    track = "CAN"

    generate_track(year, track, "#605B56", "#837a75")
