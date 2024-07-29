import os

MAIN_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PYTHON_PROJECT_ROOT = os.path.join(MAIN_PROJECT_ROOT, "py")

JOBS_DIR = os.path.join(MAIN_PROJECT_ROOT, 'temporary', 'jobs')