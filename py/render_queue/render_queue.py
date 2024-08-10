import logging
import os
import shutil
import sys
import time

# add project root directory to the system path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import main_entry
import query
from utils.project_structure import JOBS_DIR

logger = logging.getLogger(__name__)

STAGING_DIR = os.path.join(JOBS_DIR, "staging")
IN_PROGRESS_DIR = os.path.join(JOBS_DIR, "in_progress")
COMPLETED_DIR = os.path.join(JOBS_DIR, "completed")


def get_oldest_file(directory):
    files = [f for f in os.listdir(directory) if f.endswith(".yaml")]
    if not files:
        return None
    return min(files, key=lambda f: os.path.getmtime(os.path.join(directory, f)))


# returns whether we should sleep or not, if we just processed a job
# then we don't want to sleep because there may be many items in queue
def process_next_job():
    job_file = get_oldest_file(STAGING_DIR)
    if not job_file:
        logger.info("No jobs in staging.")
        return True

    staging_path = os.path.join(STAGING_DIR, job_file)
    in_progress_path = os.path.join(IN_PROGRESS_DIR, job_file)
    finished_path = os.path.join(COMPLETED_DIR, job_file)
    # Move to in_progress
    shutil.move(staging_path, in_progress_path)
    logger.info(f"Job {job_file} moved to in_progress")

    # Process the job
    main_entry.main(in_progress_path)

    # Move to finished
    shutil.move(in_progress_path, finished_path)
    logger.info(f"Job {job_file} completed and moved to finished")


def run_queue():
    logger.info("Job queue system started. Checking for jobs every 5 minutes...")
    while True:
        # we want to run jobs in staging before checking for others,
        # this is to make testing easier
        logger.info("Checking for jobs...")
        should_sleep = process_next_job()

        # each time we also need to check if the new data is ready
        # query.main()  # this will automatically job in staging
        if should_sleep:
            logger.info("Sleeping for 5 minutes...")
            time.sleep(300)


if __name__ == "__main__":
    run_queue()

