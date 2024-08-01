import os

MAIN_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PYTHON_PROJECT_ROOT = os.path.join(MAIN_PROJECT_ROOT, "py")

JOBS_DIR = os.path.join(MAIN_PROJECT_ROOT, "temporary", "jobs")

# within persistent/data
DATA_DIR = os.path.join(MAIN_PROJECT_ROOT, "persistent", "data")
TRACK_DATA_DIR = os.path.join(DATA_DIR, "track_data")
DRIVER_IMAGES_DIR = os.path.join(DATA_DIR, "driver_images")
DRIVER_TIMES_DIR = os.path.join(DATA_DIR, "driver_times")
CAR_DATA_DIR = os.path.join(DATA_DIR, "car_data")


def get_car_data_dir(year: str, track: str, fps: str) -> str:
    return os.path.join(CAR_DATA_DIR, f"{year}_{track}_{fps}")


def get_car_data_path(year: str, track: str, fps: str, driver: str) -> str:
    return os.path.join(get_car_data_dir(year, track, fps), f"{driver}.csv")


def get_driver_times_path(year: str, track: str) -> str:
    return os.path.join(DRIVER_TIMES_DIR, f"{year}_{track}.json")


def get_track_data_path(year: str, track: str) -> str:
    return os.path.join(TRACK_DATA_DIR, f"{year}_{track}.csv")


def get_driver_image_path(driver_name: str) -> str:
    return os.path.join(DRIVER_IMAGES_DIR, f"{driver_name}.png")
