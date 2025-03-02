"""Upload to YouTube."""

import json
import os

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from py.socials import youtube_metadata
from py.utils.config import Config, YouTubeConfig

# Local token storage file
TOKEN_FILE = "youtube_token.json"
# YouTube API OAuth scopes
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def get_authenticated_youtube(yt_config: YouTubeConfig):
    """Get authenticated YouTube service that works in both local and CI environments."""
    # Check if we're running in GitHub Actions
    in_github_actions = os.environ.get("GITHUB_ACTIONS") == "true"

    credentials = None

    if in_github_actions:
        # In GitHub Actions: Use secrets to create credentials
        credentials = Credentials(
            token=None,  # We'll force a refresh
            refresh_token=os.environ.get("YOUTUBE_REFRESH_TOKEN"),
            token_uri="https://oauth2.googleapis.com/token",
            client_id=os.environ.get("YOUTUBE_CLIENT_ID"),
            client_secret=os.environ.get("YOUTUBE_CLIENT_SECRET"),
            scopes=SCOPES,
        )
        # Force a refresh to get a new access token
        credentials.refresh(Request())
    else:
        # Local development: Use saved token file or interactive flow
        if os.path.exists(TOKEN_FILE):
            with open(TOKEN_FILE, "r") as token:
                token_data = json.load(token)
                credentials = Credentials.from_authorized_user_info(token_data, SCOPES)

        # If no valid credentials, run the OAuth flow
        if not credentials or not credentials.valid:
            if credentials and credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    yt_config["client_secret_path"], SCOPES
                )
                credentials = flow.run_local_server(port=0)

            # Save the credentials for future local runs
            with open(TOKEN_FILE, "w") as token:
                token.write(credentials.to_json())

    # Return the YouTube API client
    return build("youtube", "v3", credentials=credentials)


def main(config: Config, mp4_filepath: str):
    """Upload a video to YouTube using the provided configuration and file path.

    Args:
        config: Configuration object containing YouTube API credentials and upload settings
        mp4_filepath: Path to the MP4 file to upload

    Returns:
        str: URL of the uploaded YouTube video

    Raises:
        ValueError: If YouTube configuration is missing or upload fails

    """
    yt_config = config["socials"]["youtube"]
    if not yt_config:
        raise ValueError("YouTube configuration not found in config file")

    youtube = get_authenticated_youtube(yt_config)
    body = youtube_metadata.main(config)

    media = MediaFileUpload(mp4_filepath, mimetype="video/mp4", resumable=True)
    request = youtube.videos().insert(
        part=",".join(body.keys()), body=body, media_body=media
    )

    response = request.execute()

    if not response or "id" not in response:
        raise ValueError("YouTube upload failed - received invalid response")

    video_id = response["id"]
    video_url = f"https://www.youtube.com/watch?v={video_id}"

    return video_url
