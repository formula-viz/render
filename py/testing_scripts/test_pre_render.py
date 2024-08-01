import logging
import os
import subprocess
import sys

import pandas as pd

# add project root directory to the system path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.project_structure import get_track_data_path
from utils.read_yaml import read_yaml

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def run_command(command):
    try:
        subprocess.run(command, check=True, shell=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed: {e}")
        sys.exit(1)


import matplotlib.pyplot as plt
import pandas as pd


def plot_inner_outer_lines(df):
    # Check if the required columns exist
    required_columns = ["inner_X", "inner_Y", "outer_X", "outer_Y"]
    if not all(col in df.columns for col in required_columns):
        raise ValueError("DataFrame must contain inner_X, inner_Y, outer_X, and outer_Y columns")

    # Create a new figure and axis
    fig, ax = plt.subplots(figsize=(10, 6))

    # Plot inner line
    ax.plot(df["inner_X"], df["inner_Y"], label="Inner Line", color="blue")

    # Plot outer line
    ax.plot(df["outer_X"], df["outer_Y"], label="Outer Line", color="red")

    # Add labels and title
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_title("Inner and Outer Lines Plot")

    # Add legend
    ax.legend()

    # Show grid
    ax.grid(True, linestyle="--", alpha=0.7)

    # Show plot
    plt.tight_layout()
    plt.show()


def main():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Construct the full path to test.yaml
    yaml_path = os.path.join(current_dir, "test.yaml")

    # now, we want to visualize the output from pre_render
    # the main thing is the track data, we'll visualize using matplotlib
    run_command(f"python3 ../pre_render/pre_render.py {yaml_path}")

    # we will need to grab the config to see the output location
    year, track, fps, drivers, config = read_yaml(yaml_path)
    track_data_path = get_track_data_path(str(year), track)
    track_data = pd.read_csv(track_data_path)

    # we can plot the track data
    plot_inner_outer_lines(track_data)


main()
