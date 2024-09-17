import json
import os
import subprocess
import sys

MAIN_PROJECT_ROOT = os.path.dirname(os.path.realpath(__file__))
PYTHON_SCRIPTS_ROOT = os.path.join(MAIN_PROJECT_ROOT, "py")
sys.path.append(MAIN_PROJECT_ROOT)
sys.path.append(PYTHON_SCRIPTS_ROOT)
sys.path.append(os.path.dirname(os.path.realpath(__file__)))

from utils.config import Config


def run_blender_script(blender_path, script_path, config: Config):
    # Expand user directory if necessary
    script_path = os.path.expanduser(script_path)

    # Convert config to JSON string
    config_json = json.dumps(config.to_dict())

    # Construct the full command
    full_command = [
        blender_path,
        "--background",
        "--python",
        script_path,
        "--",  # Separate Blender arguments from script arguments
        config_json,
    ]

    # Run the Blender process
    try:
        result = subprocess.run(full_command, check=True, capture_output=True, text=True)
        print(f"Blender script output for {script_path}:", result.stdout)
        return {"status": "success", "output": result.stdout}
    except subprocess.CalledProcessError as e:
        error_message = f"Error running Blender script {script_path}: {e}\nError output: {e.stderr}"
        print(error_message)
        return {"status": "error", "message": error_message}


def run_blender_pipeline(blender_path, script_paths, config: Config):
    results = []
    for script_path in script_paths:
        result = run_blender_script(blender_path, script_path, config)
        results.append(result)
        if result["status"] == "error":
            break  # Stop the pipeline if an error occurs
    return results


def run_job(config: Config):
    blender_path = "/usr/bin/blender"
    script_paths = [
        "~/Projects/formula-viz/render/py/render/render.py",
        "~/Projects/formula-viz/render/py/post_render/post_render.py",
    ]
    results = run_blender_pipeline(blender_path, script_paths, config)
    return results
