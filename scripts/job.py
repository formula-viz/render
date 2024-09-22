import json
import os
import subprocess

from utils.config import Config

def run_blender_script(blender_path, script_path, config: Config):
    script_path = os.path.expanduser(script_path)

    config_json = json.dumps(config.to_dict())

    full_command = [
        blender_path,
        "--background",
        "--python",
        script_path,
        "--",  # Separate Blender arguments from script arguments
        config_json,
    ]

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
            break
    return results


def run_job(config: Config):
    blender_path = "/usr/bin/blender"
    script_paths = [
        os.environ.get("RENDER_PY"),
        os.environ.get("POSTRENDER_PY"),
    ]
    results = run_blender_pipeline(blender_path, script_paths, config)
    return results
