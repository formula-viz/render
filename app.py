import os
import sys
import site

print("From app.py")
print("Python executable:", sys.executable)
print("Python version:", sys.version)
print("Sys.path:", sys.path)
print("Site packages:", site.getsitepackages())

import yaml
from flask import Flask, jsonify, request
from redis import Redis
from rq import Queue

from job import run_job

MAIN_PROJECT_ROOT = os.path.dirname(os.path.realpath(__file__))
PYTHON_SCRIPTS_ROOT = os.path.join(
    MAIN_PROJECT_ROOT,
    "py",
)
sys.path.append(MAIN_PROJECT_ROOT)
sys.path.append(PYTHON_SCRIPTS_ROOT)
sys.path.append(os.path.dirname(os.path.realpath(__file__)))

from utils.config import Config

app = Flask(__name__)

# Redis Configuration
redis_host = "localhost"
redis_port = 6379
redis_db = 0

# Blender Configuration
blender_path = "/path/to/blender"
script_path = os.path.join(MAIN_PROJECT_ROOT, "blender_script.py")

# Initialize Redis connection
redis_client = Redis(host=redis_host, port=redis_port, db=redis_db)
redis_client.ping()  # Test the connection

# Initialize Redis Queue
queue = Queue(connection=redis_client)


@app.route("/render", methods=["POST"])
def render():
    try:
        if request.headers.get("Content-Type") != "application/yaml":
            return jsonify({"status": "error", "message": "Content-Type must be application/yaml"}), 400

        yaml_data = yaml.safe_load(request.data)
        config = Config(yaml_data)

        # Enqueue the rendering job
        job = queue.enqueue(run_job, args=(config,))  # Set an appropriate timeout

        result = {"status": "success", "message": "Render job enqueued", "job_id": job.id}
        return jsonify(result), 202  # 202 Accepted
    except Exception as e:
        error_message = f"An error occurred: {str(e)}"
        print(error_message)
        return jsonify({"status": "error", "message": error_message}), 500


@app.route("/job_status/<job_id>", methods=["GET"])
def job_status(job_id):
    job = queue.fetch_job(job_id)
    if job is None:
        return jsonify({"status": "error", "message": "Job not found"}), 404

    if job.is_finished:
        return jsonify({"status": "completed", "result": job.result}), 200
    elif job.is_failed:
        return jsonify({"status": "failed", "message": str(job.exc_info)}), 500
    else:
        return jsonify({"status": "in_progress"}), 202


if __name__ == "__main__":
    app.run(debug=True)
