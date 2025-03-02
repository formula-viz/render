"""Start Formula Viz rendering and publishing process."""

import json
import os
import subprocess
import sys
from pathlib import Path

from py.post_process.post_process import post_process
from py.socials import youtube_upload


def main():
    """Start Formula Viz rendering and publishing process."""
    project_root = Path(__file__).parent.absolute()

    os.environ["PYTHONPATH"] = (
        f"{project_root}:{project_root}/py:{os.environ.get('PYTHONPATH', '')}"
    )

    config_file = project_root / "config.json"
    template_file = project_root / "config-template.json"

    def get_config(file):
        with open(file, "r") as f:
            return json.load(f)

    config = (
        get_config(config_file) if config_file.exists() else get_config(template_file)
    )

    ui_mode = config.get("dev_settings", {}).get("ui_mode", False)

    try:
        cmd = ["blender"]
        if not ui_mode:
            cmd.append("-b")  # Background mode if not UI mode

        cmd.extend(
            [
                "--python",
                f"{project_root}/py/render/render.py",
                "--",
                json.dumps(config),
            ]
        )

        subprocess.run(cmd, check=True)

        mp4_filepath = post_process(config)
        yt_url = youtube_upload.main(config, mp4_filepath)

        print(f"Video uploaded to {yt_url}")

        return 0
    except subprocess.CalledProcessError as e:
        print(f"Blender exited with error code {e.returncode}")
        return e.returncode


if __name__ == "__main__":
    sys.exit(main())
