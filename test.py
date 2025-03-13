import os
import subprocess
import sys
from pathlib import Path

def main(run_external_api_flags: bool = False):
    project_root = Path(__file__).parent.absolute()

    os.environ["PYTHONPATH"] = (
        f"{project_root}:{project_root}/py:{os.environ.get('PYTHONPATH', '')}"
    )

    try:
        cmd = ["blender"]
        cmd.extend(
            [
                "-b",
                "--python",
                f"{project_root}/tests/run_tests.py",
            ]
        )

        if run_external_api_flags:
            cmd.extend(["--", "--run-external-api-flags"])

        subprocess.run(cmd, check=True)
        return 0
    except subprocess.CalledProcessError as e:
        print(f"Blender exited with error code {e.returncode}")
        return e.returncode


if __name__ == "__main__":
    if "--run-external-api-flags" in sys.argv:
        sys.exit(main(run_external_api_flags=True))
    else:
        sys.exit(main(run_external_api_flags=False))
