import yaml
from flask import Flask, jsonify, request
from job import run_job
from redis import Redis
from rq import Queue
from utils.config import Config

app = Flask(__name__)

# Redis Configuration
redis_host = "localhost"
redis_port = 6379
redis_db = 0

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

        job = queue.enqueue(run_job, args=(config,), timeout=36000)

        result = {"status": "success", "message": "Render job enqueued", "job_id": job.id}
        return jsonify(result), 202
    except Exception as e:
        error_message = f"An error occurred: {str(e)}"
        print(error_message)
        return jsonify({"status": "error", "message": error_message}), 500


# In the future this could include more useful data such as
# the current running time of the present job, # of queued jobs, etc.
# @app.route("/job_status/<job_id>", methods=["GET"])
# def job_status(job_id):
#     job = queue.fetch_job(job_id)
#     if job is None:
#         return jsonify({"status": "error", "message": "Job not found"}), 404
#
#     if job.is_finished:
#         return jsonify({"status": "completed", "result": job.result}), 200
#     elif job.is_failed:
#         return jsonify({"status": "failed", "message": str(job.exc_info)}), 500
#     else:
#         return jsonify({"status": "in_progress"}), 202

if __name__ == "__main__":
    app.run(debug=True)
