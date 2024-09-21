import os

RESOURCES_DIR = os.environ.get("RESOURCES_DIR")
CAR_DATA_DIR = os.environ.get("CAR_DATA_DIR")
DRIVER_TIMES_DIR = os.environ.get("DRIVER_TIMES_DIR")
DRIVER_IMAGES_DIR = os.environ.get("DRIVER_IMAGES_DIR")
FRAMES_DIR = os.environ.get("FRAMES_DIR")


def get_frames_dir():
    return FRAMES_DIR


class DriverData:
    @staticmethod
    def get_car_data_dir(year: str, track: str, fps: str) -> str:
        return os.path.join(CAR_DATA_DIR, f"{year}_{track}_{fps}")

    @staticmethod
    def get_car_data_path(year: str, track: str, fps: str, driver: str) -> str:
        return os.path.join(DriverData.get_car_data_dir(year, track, fps), f"{driver}.csv")

    @staticmethod
    def get_driver_times_path(year: str, track: str) -> str:
        return os.path.join(DRIVER_TIMES_DIR, f"{year}_{track}.json")

    @staticmethod
    def get_driver_image_path(driver_abbrev: str) -> str:
        return os.path.join(DRIVER_IMAGES_DIR, f"{driver_abbrev}.png")


TRACK_DATA_DIR = os.environ.get("TRACK_DATA_DIR")


class TrackData:
    @staticmethod
    def get_track_data_path(year: str, track: str) -> str:
        return os.path.join(TRACK_DATA_DIR, f"{year}_{track}.csv")


BACKGROUND_MUSIC_PATH = os.environ.get("BACKGROUND_MUSIC_PATH")
BACKGROUND_IMAGE_PATH = os.environ.get("BACKGROUND_IMAGE_PATH")
MAIN_FONT = os.environ.get("MAIN_FONT")
CAR_FBX_PATH = os.environ.get("CAR_FBX_PATH")
CAR_PAINTS_DIR = os.environ.get("CAR_PAINTS_DIR")
CAR_TEXTURES_DIR = os.environ.get("CAR_TEXTURES_DIR")


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
