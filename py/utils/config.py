"""Casts the raw json configuration of the application into specific types for language server support."""

from typing import List, Literal, TypedDict


class DevelopmentConfig(TypedDict):
    """Handles the conditional invocations of the separate modules."""

    ui_mode: bool
    quick_textures_mode: bool
    limited_frames_mode: bool


class RenderConfig(TypedDict):
    """Handles the configuration of the final render / output."""

    engine: str
    fps: int
    samples: int
    is_shorts_output: bool
    output: str
    max_cam_distance: int
    start_buffer_frames: int
    end_buffer_frames: int


class Config(TypedDict):
    """Handles general configuration and holds the specific configuration classes.

    Contains general fields (track, year, type, drivers),
    development configuration (),
    and render settings (engine, fps, output format).
    """

    track: str
    year: int
    _type: str
    type: Literal["head-to-head", "rest-of-field"]
    dev_settings: DevelopmentConfig
    render: RenderConfig
    drivers: List[str]
