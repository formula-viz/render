import os
from pathlib import Path

# Get project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Define directory structures
TEMPORARY_DIR = PROJECT_ROOT / "temporary"
RESOURCES_DIR = PROJECT_ROOT / "persistent/resources"
DATA_DIR = PROJECT_ROOT / "persistent/data"
CSV_REPO_DIR = PROJECT_ROOT / "csv_repo"

# Car related paths
CAR_FBX_PATH = str(
    RESOURCES_DIR / "cars/formula-1-2024-generic/source/F1_TexPaintBlender_v01_20210215.fbx")
CAR_PAINTS_DIR = str(TEMPORARY_DIR / "car_paints")
CAR_TEXTURES_DIR = str(RESOURCES_DIR / "cars/formula-1-2024-generic/textures")

# Crown path
CROWN_GLB_PATH = str(RESOURCES_DIR / "king_crown.glb")

# Data directories
CAR_DATA_DIR = str(DATA_DIR / "car_data")
DRIVER_TIMES_DIR = str(DATA_DIR / "driver_times")
DRIVER_IMAGES_DIR = str(DATA_DIR / "driver_images")
TRACK_DATA_DIR = str(CSV_REPO_DIR / "track_data")

# Resource paths
BACKGROUND_MUSIC_PATH = str(RESOURCES_DIR / "audio/lofi-hiphop-background.m4a")
BACKGROUND_IMAGE_PATH = str(RESOURCES_DIR / "backgrounds/background1.jpeg")
MAIN_FONT = str(RESOURCES_DIR / "fonts/Formula1-Regular.ttf")
BOLD_FONT = str(RESOURCES_DIR / "fonts/Formula1-Bold.ttf")

# Output directories
FRAMES_DIR = str(TEMPORARY_DIR / "frames")
OUTPUT_DIR = str(PROJECT_ROOT / "output")

# Python script paths
RENDER_PY = str(PROJECT_ROOT / "py/render/render.py")
POSTRENDER_PY = str(PROJECT_ROOT / "py/post_render/post_render.py")

# Rest of your classes remain the same, but now use the variables defined above


class DriverDataPS:
    @staticmethod
    def get_car_data_dir(year: str, track: str, fps: str) -> str:
        return os.path.join(CAR_DATA_DIR, f"{year}_{track}_{fps}")

    @staticmethod
    def get_car_data_path(year: str, track: str, fps: str, driver: str) -> str:
        return os.path.join(DriverDataPS.get_car_data_dir(year, track, fps), f"{driver}.csv")

    @staticmethod
    def get_driver_times_path(year: str, track: str) -> str:
        return os.path.join(DRIVER_TIMES_DIR, f"{year}_{track}.json")

    @staticmethod
    def get_driver_image_path(driver_abbrev: str) -> str:
        return os.path.join(DRIVER_IMAGES_DIR, f"{driver_abbrev}.png")


class TrackDataPS:
    @staticmethod
    def get_track_data_dir() -> str:
        return TRACK_DATA_DIR

    @staticmethod
    def get_year_of_track_file(track_file: str) -> int:
        return track_file.split("_")[1].split(".")[0]

    @staticmethod
    def get_track_file(year: str, track: str) -> str:
        return f"{year}_{track}.csv"


class Resources:
    @staticmethod
    def get_background_image_path():
        return BACKGROUND_IMAGE_PATH

    @staticmethod
    def get_background_music_path():
        return BACKGROUND_MUSIC_PATH

    @staticmethod
    def get_main_font():
        return MAIN_FONT

    @staticmethod
    def get_bold_font():
        return BOLD_FONT

    @staticmethod
    def get_car_fbx_path():
        return CAR_FBX_PATH

    @staticmethod
    def get_car_textures_dir():
        return CAR_TEXTURES_DIR

    @staticmethod
    def get_car_paints_dir():
        return CAR_PAINTS_DIR

    @staticmethod
    def get_new_texture_image_path(driver_abbrev: str, blender_obj_name: str) -> str:
        return os.path.join(CAR_PAINTS_DIR, f"{driver_abbrev}_{blender_obj_name}.png")

    @staticmethod
    def get_crown_path():
        return CROWN_GLB_PATH


def ensure_directories_exist():
    """Create all necessary directories if they don't exist."""
    directories = [
        TEMPORARY_DIR,
        CAR_PAINTS_DIR,
        FRAMES_DIR,
        OUTPUT_DIR
    ]
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)


# Create directories when module is imported
ensure_directories_exist()
