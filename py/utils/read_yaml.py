import yaml
from logger import logger


def read_yaml(yaml_path):
    try:
        with open(yaml_path, "r") as file:
            config = yaml.safe_load(file)

        year = config["year"]
        track = config["track"]
        fps = config["render"]["fps"]

        if not isinstance(year, int):
            raise ValueError(f"Year must be an integer, got {type(year)}")
        if not isinstance(track, str):
            raise ValueError(f"Track must be a string, got {type(track)}")
        if not isinstance(fps, int):
            raise ValueError(f"FPS must be an integer, got {type(fps)}")

        drivers = []
        for driver in config["drivers"]:
            name = driver["name"]
            color = driver["color"]
            if not isinstance(name, str) or not isinstance(color, str):
                raise ValueError(f"Driver name and color must be strings, got {type(name)} and {type(color)}")
            drivers.append((name, color))

        logger.info("Received Config:")
        logger.info(f"    Year: {year}")
        logger.info(f"    Track: {track}")
        logger.info(f"    FPS: {fps}")
        logger.info("Drivers:")
        for driver in drivers:
            logger.info(f"    {driver}")

        return year, track, fps, drivers, config

    except yaml.YAMLError as e:
        logger.error(f"Error parsing YAML file: {e}")
        raise
    except KeyError as e:
        logger.error(f"Missing required key in YAML file: {e}")
        raise
    except ValueError as e:
        logger.error(f"Invalid data type in YAML file: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error reading YAML file: {e}")
        raise
