import os

MAIN_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PYTHON_PROJECT_ROOT = os.path.join(MAIN_PROJECT_ROOT, "py")

TEMPORARY_DIR = os.path.join(MAIN_PROJECT_ROOT, "temporary")
CAR_PAINTS_DIR = os.path.join(TEMPORARY_DIR, "car_paints")
JOBS_DIR = os.path.join(MAIN_PROJECT_ROOT, "temporary", "jobs")
STAGING_DIR = os.path.join(JOBS_DIR, "staging")
IN_PROGRESS_DIR = os.path.join(JOBS_DIR, "in_progress")
COMPLETED_DIR = os.path.join(JOBS_DIR, "completed")

# resources
RESOURCES_DIR = os.path.join(MAIN_PROJECT_ROOT, "persistent", "resources")

# within persistent/data
DATA_DIR = os.path.join(MAIN_PROJECT_ROOT, "persistent", "data")
TRACK_DATA_DIR = os.path.join(DATA_DIR, "track_data")
DRIVER_IMAGES_DIR = os.path.join(DATA_DIR, "driver_images")
DRIVER_TIMES_DIR = os.path.join(DATA_DIR, "driver_times")
CAR_DATA_DIR = os.path.join(DATA_DIR, "car_data")

TRACKS_FILE = os.path.join(PYTHON_PROJECT_ROOT, "render_queue", "tracks.txt")
CUR_YEAR = 2024

FORMULA_ONE_REGULAR_FONT_PATH = os.path.join(RESOURCES_DIR, "fonts", "Formula1-Regular.ttf")
BACKGROUND_ONE_PATH = os.path.join(RESOURCES_DIR, "backgrounds", "background1.jpeg")


def get_fish_venv_path() -> str:
    return os.path.join(PYTHON_PROJECT_ROOT, "venv", "bin", "activate.fish")


def get_bash_venv_path() -> str:
    return os.path.join(PYTHON_PROJECT_ROOT, "venv", "bin", "activate")

def get_requirements_path() -> str:
    return os.path.join(PYTHON_PROJECT_ROOT, "requirements.txt")

def get_render_path() -> str:
    return os.path.join(PYTHON_PROJECT_ROOT, "render", "render.py")

def get_post_render_path() -> str:
    return os.path.join(PYTHON_PROJECT_ROOT, "post_render", "post_render.py")

def get_pre_render_path() -> str:
    return os.path.join(PYTHON_PROJECT_ROOT, "pre_render", "pre_render.py")


# where part is chassis, applicances, etc.
def get_car_paints_path(driver_abbrev: str, part: str) -> str:
    return os.path.join(CAR_PAINTS_DIR, f"{driver_abbrev}_{part}.png")


def get_car_fbx_path() -> str:
    return os.path.join(
        RESOURCES_DIR, "cars", "formula-1-2024-generic", "source", "F1_TexPaintBlender_v01_20210215.fbx"
    )


def get_car_textures_dir() -> str:
    return os.path.join(RESOURCES_DIR, "cars", "formula-1-2024-generic", "textures")


def get_car_data_dir(year: str, track: str, fps: str) -> str:
    return os.path.join(CAR_DATA_DIR, f"{year}_{track}_{fps}")


def get_car_data_path(year: str, track: str, fps: str, driver: str) -> str:
    return os.path.join(get_car_data_dir(year, track, fps), f"{driver}.csv")


def get_driver_times_path(year: str, track: str) -> str:
    return os.path.join(DRIVER_TIMES_DIR, f"{year}_{track}.json")


def get_track_data_path(year: str, track: str) -> str:
    return os.path.join(TRACK_DATA_DIR, f"{year}_{track}.csv")


def get_driver_image_path(driver_abbrev: str) -> str:
    return os.path.join(DRIVER_IMAGES_DIR, f"{driver_abbrev}.png")

def get_background_music_path() -> str:
    return os.path.join(RESOURCES_DIR, "audio", "lofi-hiphop-background.m4a")

def get_frames_dir() -> str:
    return os.path.join(TEMPORARY_DIR, "frames")
