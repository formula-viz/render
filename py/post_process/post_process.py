"""Add background msuic to blender rendered video."""

import os
import subprocess
from typing import Optional

from py.utils.config import Config
from py.utils.logger import log_err, log_info
from py.utils.project_structure import BACKGROUND_MUSIC_PATH, OutputsManager


def add_background_music(
    render_output_path: str,
    post_process_output_path: str,
    music_fadeout_seconds: int = 5,
    alternate_background_music_path: Optional[str] = None,
):
    """Add background music to a rendered video using FFmpeg with a 5-second fade out at the end.

    Args:
        render_output_path: Path to the input video
        post_process_output_path: Path to save the output video
        alternate_background_music_path: Path to the music file (optional)

    Returns:
        Path to the processed video with music

    """
    if not os.path.exists(render_output_path):
        raise FileNotFoundError(f"Video file not found: {render_output_path}")

    music_path = alternate_background_music_path or BACKGROUND_MUSIC_PATH
    if not os.path.exists(music_path):
        raise FileNotFoundError(f"Music file not found: {music_path}")

    log_info(
        f"Adding background music to video: {os.path.basename(render_output_path)}"
    )
    log_info(f"Using music: {os.path.basename(music_path)}")
    log_info(f"Output path: {post_process_output_path}")

    # Get the duration of the video to calculate fade out start time
    duration_cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        render_output_path,
    ]

    try:
        duration_output = subprocess.run(
            duration_cmd, check=True, capture_output=True, text=True
        )
        video_duration = float(duration_output.stdout.strip())
        fade_start = max(0, video_duration - 5)  # Start fade 5 seconds from the end
    except (subprocess.CalledProcessError, ValueError) as e:
        log_err(f"Error getting video duration: {e}")
        raise e

    cmd = [
        "ffmpeg",
        "-i",
        render_output_path,
        "-i",
        music_path,
        "-c:v",
        "copy",  # Copy video stream
        "-af",
        f"afade=t=out:st={fade_start}:d={music_fadeout_seconds}",  # Add fade out effect to audio
        "-shortest",  # trim to the shortest input
        "-y",  # Overwrite output if exists
        post_process_output_path,
    ]

    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        log_info("Successfully added background music with fade out")
    except subprocess.CalledProcessError as e:
        log_err(f"Error adding background music: {e.stderr}")
        raise RuntimeError(f"Failed to add background music: {str(e)}")


def post_process(config: Config) -> str:
    """Post process video and output to same video_path.

    Args:
        config: Config
        video_path: Path to the video to process

    Returns:
        Path to the processed video

    """
    log_info("Starting post-processing")
    render_output_path = OutputsManager.get_render_output(config)
    post_process_output_path = OutputsManager.get_post_process_output(config)
    music_fadeout_seconds = config["post_process"]["music_fadeout_seconds"]

    add_background_music(
        str(render_output_path), str(post_process_output_path), music_fadeout_seconds
    )
    log_info("Post-processing complete")

    return config["post_process"]["output"]
