from pathlib import Path

from py.utils.config import Config

# Get project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Define directory structures
TEMPORARY_DIR = PROJECT_ROOT / "temporary"
RESOURCES_DIR = PROJECT_ROOT / "persistent/resources"
DATA_DIR = PROJECT_ROOT / "persistent/data"
CSV_REPO_DIR = PROJECT_ROOT / "csv_repo"

# Car related paths
F1_CAR_BLEND_PATH = RESOURCES_DIR / "cars/f1-car-2024.blend"
CAR_PAINTS_DIR = RESOURCES_DIR / "cars/alternate_textures"
FORMULA_VIZ_CAR_PATH = RESOURCES_DIR / "cars/formula_viz_car.blend"

# Crown path
CROWN_GLB_PATH = RESOURCES_DIR / "king_crown.glb"

# Data directories
CAR_DATA_DIR = DATA_DIR / "car_data"
DRIVER_TIMES_DIR = DATA_DIR / "driver_times"
DRIVER_IMAGES_DIR = DATA_DIR / "driver_images"
TRACK_DATA_DIR = CSV_REPO_DIR / "track_data"

# Resource paths
BACKGROUND_MUSIC_PATH = RESOURCES_DIR / "audio/lofi-hiphop-background.m4a"
BACKGROUND_IMAGE_PATH = RESOURCES_DIR / "backgrounds/background1.jpeg"
MAIN_FONT = RESOURCES_DIR / "fonts/Formula1-Regular.ttf"
BOLD_FONT = RESOURCES_DIR / "fonts/Formula1-Bold.ttf"

# Output directories
FRAMES_DIR = TEMPORARY_DIR / "frames"
OUTPUT_DIR = PROJECT_ROOT / "output"

# Python script paths
RENDER_PY = PROJECT_ROOT / "py/render/render.py"

# Social Media Icons
SOCIAL_ICONS_DIR = RESOURCES_DIR / "social_icons"
YOUTUBE_ICON_PATH = SOCIAL_ICONS_DIR / "youtube.png"
DISCORD_ICON_PATH = SOCIAL_ICONS_DIR / "discord.webp"
INSTAGRAM_ICON_PATH = SOCIAL_ICONS_DIR / "instagram.png"
TIKTOK_ICON_PATH = SOCIAL_ICONS_DIR / "tiktok.webp"


class OutputsManager:
    @staticmethod
    def get_render_output(config: Config) -> Path:
        return OUTPUT_DIR / config["render"]["output"]

    @staticmethod
    def get_post_process_output(config: Config) -> Path:
        return OUTPUT_DIR / config["post_process"]["output"]


class DriverDataPS:
    @staticmethod
    def get_car_data_dir(year: str, track: str, fps: str) -> Path:
        return CAR_DATA_DIR / f"{year}_{track}_{fps}"

    @staticmethod
    def get_car_data_path(year: str, track: str, fps: str, driver: str) -> Path:
        return DriverDataPS.get_car_data_dir(year, track, fps) / f"{driver}.csv"

    @staticmethod
    def get_driver_times_path(year: str, track: str) -> Path:
        return DRIVER_TIMES_DIR / f"{year}_{track}.json"

    @staticmethod
    def get_driver_image_path(driver_abbrev: str) -> Path:
        return DRIVER_IMAGES_DIR / f"{driver_abbrev}.png"


class TrackDataPS:
    @staticmethod
    def get_track_data_dir() -> Path:
        return TRACK_DATA_DIR

    @staticmethod
    def get_year_of_track_file(track_file: str) -> int:
        return int(track_file.split("_")[1].split(".")[0])

    @staticmethod
    def get_track_file(year: str, track: str) -> str:
        return f"{year}_{track}.csv"


class Resources:
    @staticmethod
    def get_background_image_path() -> Path:
        return BACKGROUND_IMAGE_PATH

    @staticmethod
    def get_background_music_path() -> Path:
        return BACKGROUND_MUSIC_PATH

    @staticmethod
    def get_main_font() -> Path:
        return MAIN_FONT

    @staticmethod
    def get_bold_font() -> Path:
        return BOLD_FONT

    @staticmethod
    def get_car_paints_dir() -> Path:
        return CAR_PAINTS_DIR

    @staticmethod
    def get_new_texture_image_path(blender_obj_name, hex_color) -> Path:
        return CAR_PAINTS_DIR / f"{blender_obj_name.split('-')[-1]}_{hex_color}.png"

    @staticmethod
    def get_crown_path() -> Path:
        return CROWN_GLB_PATH


def ensure_directories_exist():
    """Create all necessary directories if they don't exist."""
    directories = [
        TEMPORARY_DIR,
        CAR_PAINTS_DIR,
        FRAMES_DIR,
        OUTPUT_DIR,
        DATA_DIR,
        CAR_DATA_DIR,
        DRIVER_TIMES_DIR,
        DRIVER_IMAGES_DIR,
        TRACK_DATA_DIR,
    ]
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)


# Create directories when module is imported
ensure_directories_exist()
