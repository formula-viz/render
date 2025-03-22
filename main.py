"""Start Formula Viz rendering and publishing process."""

import json
import os
import subprocess
import sys
from pathlib import Path

from py.post_process.post_process import post_process
from py.socials import youtube_upload
from py.utils.logger import log_err, log_info


def run_for_config(config, project_root):
    """Run the rendering process for a given configuration."""
    ui_mode = config.get("dev_settings", {}).get("ui_mode", False)

    def trigger(config):
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

            if not ui_mode:
                mp4_filepath = post_process(config)
                yt_url = youtube_upload.main(
                    config, os.path.join("output", mp4_filepath)
                )
                print(f"Video uploaded to {yt_url}")

            return 0
        except subprocess.CalledProcessError as e:
            print(f"Blender exited with error code {e.returncode}")
            return e.returncode

    if config["render"]["is_both_mode"]:
        config["render"]["is_shorts_output"] = True
        trigger(config)
        config["render"]["is_shorts_output"] = False
        trigger(config)
    else:
        trigger(config)


def run_single_mode(project_root):
    """Load configuration and set up the environment for the rendering process."""
    config_file = project_root / "config.json"
    template_file = project_root / "config-template.json"

    def get_config(file: Path):
        with open(file, "r") as f:
            return json.load(f)

    config = (
        get_config(config_file) if config_file.exists() else get_config(template_file)
    )

    run_for_config(config, project_root)


def run_batch_mode(project_root):
    """Run batch mode, meaning a group of configurations."""
    batch_configs_dir = project_root / "batch_configs"
    if not batch_configs_dir.exists():
        log_err(f"Batch configs directory not found: {batch_configs_dir}")
        return 1

    config_files = [f for f in batch_configs_dir.glob("*.json")]
    if not config_files:
        log_err(f"No config files found in {batch_configs_dir}")
        return 1

    for config_file in config_files:
        log_info(f"Processing config: {config_file.name}")
        with open(config_file, "r") as f:
            config = json.load(f)
        run_for_config(config, project_root)
    return 0


def main():
    """Start Formula Viz rendering and publishing process."""
    project_root = Path(__file__).parent.absolute()

    os.environ["PYTHONPATH"] = (
        f"{project_root}:{project_root}/py:{os.environ.get('PYTHONPATH', '')}"
    )

    if len(sys.argv) > 1 and sys.argv[1] == "batch":
        return run_batch_mode(project_root)
    else:
        return run_single_mode(project_root)


if __name__ == "__main__":
    sys.exit(main())
