from py.pre_render import load_ff1, load_track_data
from py.utils.read_yaml import read_from_yaml
import logging
import argparse
import sys

logger = logging.getLogger(__name__)

def main(yaml_path: str) -> None:
    try:
        year, track, fps, _ = read_from_yaml(yaml_path)
        load_track_data.main(year, track)
        load_ff1.main(year, track, fps)
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process race data based on YAML configuration.")
    parser.add_argument("yaml_path", help="Path to the YAML configuration file")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    main(args.yaml_path)