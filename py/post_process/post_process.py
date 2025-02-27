"""Add background msuic to blender rendered video."""

import os
import subprocess
from typing import Optional

from py.utils.config import Config
from py.utils.logger import log_err, log_info
from py.utils.project_structure import BACKGROUND_MUSIC_PATH, OutputsManager


def add_background_music(
    config: Config,
    alternate_background_music_path: Optional[str] = None,
):
    """Add background music to a rendered video using FFmpeg.

    Args:
        config: Config
        alternate_background_music_path: Path to the music file (optional)

    Returns:
        Path to the processed video with music

    """
    render_output_path = OutputsManager.get_render_output(config)
    post_process_output_path = OutputsManager.get_post_process_output(config)

    if not os.path.exists(render_output_path):
        raise FileNotFoundError(f"Video file not found: {render_output_path}")

    music_path = BACKGROUND_MUSIC_PATH
    if not os.path.exists(music_path):
        raise FileNotFoundError(f"Music file not found: {music_path}")

    log_info(
        f"Adding background music to video: {os.path.basename(render_output_path)}"
    )
    log_info(f"Using music: {os.path.basename(music_path)}")
    log_info(f"Output path: {post_process_output_path}")

    cmd = [
        "ffmpeg",
        "-i",
        render_output_path,
        "-i",
        music_path,
        "-c:v",
        "copy",  # Copy video stream
        "-c:a",
        "copy",  # Copy audio stream
        "-shortest",  # trim to the shortest input
        "-y",  # Overwrite output if exists
        post_process_output_path,
    ]

    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        log_info("Successfully added background music")
    except subprocess.CalledProcessError as e:
        log_err(f"Error adding background music: {e.stderr}")
        raise RuntimeError(f"Failed to add background music: {str(e)}")


def post_process(config: Config):
    """Post process video and output to same video_path.

    Args:
        config: Config
        video_path: Path to the video to process

    Returns:
        Path to the processed video

    """
    log_info("Starting post-processing")
    add_background_music(config)
    log_info("Post-processing complete")
