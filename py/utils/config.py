"""Casts the raw json configuration of the application into specific types for language server support."""

from typing import List, Literal, Optional, TypedDict


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
    start_buffer_frames: int
    end_buffer_frames: int


class YouTubeConfig(TypedDict):
    """YouTube-specific configuration settings."""

    client_secret_path: str

    description: str
    category: str
    playlist: Optional[str]
    is_made_for_kids: bool
    visibility: Literal["public", "private", "unlisted"]


class InstagramConfig(TypedDict):
    """Instagram-specific configuration settings."""

    caption: str
    first_comment: Optional[str]
    location_id: Optional[str]


class TikTokConfig(TypedDict):
    """TikTok-specific configuration settings."""

    description: str
    allow_comments: bool
    allow_duet: bool
    allow_stitch: bool


class FacebookConfig(TypedDict):
    """Facebook-specific configuration settings."""

    description: str
    privacy: Literal["public", "friends", "only_me"]
    scheduled_publish_time: Optional[int]


class SocialsConfig(TypedDict):
    """Handles social media configuration for publishing the output."""

    title: str
    tags: List[str]
    thumbnail_path: Optional[str]
    youtube: Optional[YouTubeConfig]
    instagram: Optional[InstagramConfig]
    tiktok: Optional[TikTokConfig]
    facebook: Optional[FacebookConfig]


class Config(TypedDict):
    """Handles general configuration and holds the specific configuration classes.

    Contains general fields (track, year, type, drivers),
    development configuration (),
    render settings (engine, fps, output format),
    and social media publication settings.
    """

    track: str
    year: int
    _type: str
    type: Literal["head-to-head", "rest-of-field"]
    dev_settings: DevelopmentConfig
    render: RenderConfig
    socials: SocialsConfig
    drivers: List[str]
