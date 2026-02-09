# 🏎️ formula-viz

formula-viz ingests raw F1 telemetry data from qualifying sessions and converts it into cinematically rendered 3D visualizations. The system automatically:
- Processes telemetry from FastF1 API
- Constructs accurate track layouts with proper racing lines
- Positions and animates cars with precise physics-based movement
- Renders high-quality video with dynamic overlays, timing information, and leaderboards
- Publishes content to YouTube automatically via GitHub Actions

## 🚀 CICD

- Automated testing with pytest
- GPU-accelerated rendering on GitHub runners
- Continuous deployment to YouTube

## 🎬 Example
The system produces full qualifying sessions rendered in both desktop (16:9) and mobile (9:16) formats:

[![Formula 1 Visualization](https://img.youtube.com/vi/QeUI84OH63w/maxresdefault.jpg)](https://www.youtube.com/watch?v=QeUI84OH63w)
*Click the image above to link to an example video on the channel.*

- [YouTube](https://youtube.com/formula-viz)
- [Discord](https://discord.gg/formula-viz)


The entrypoint to the code is py/queue/job_queue.py, run this script with no arguments
See temporary/jobs for creating jobs. These jobs will be automatically processed by FIFO when job_queue.py is run.


![image](https://github.com/user-attachments/assets/e781afed-584b-4d34-9ce1-5fb196a043ac)
https://lucid.app/lucidchart/3ff9d657-aae5-4a6f-acec-6a1838a90743/edit?beaconFlowId=51966675D0659D6E&invitationId=inv_e3f14add-2e69-4e51-9de1-7f8d24a33023&page=0_0#

Python scripts chart: https://lucid.app/lucidchart/687d3429-3c5f-4041-8bf7-294989b853e0/edit?beaconFlowId=27B80AC90C1C9043&invitationId=inv_a960f347-b385-462b-a0c8-0c3f0694793f&page=0_0#

Config Guideline:

{
  "track": "SIN", # 3 letters by convention
  "year": 2024,
  "type": "rest-of-field", # can be "rest-of-field" or "head-to-head"
  "pipeline": {
    "isolate_module": "post_render", # can be false, "render", "post_render"
    "preview_mode": true, # blender stops before rendering, good for seeing in ui
    "quick_validate_mode": false # means a limited num of frames will run to test end to end process
  },
  "render": {
    "fps": 30,
    "samples": 32,
    "adaptive_sampling": true,
    "is_4k": true,
    "output": "output.mp4",
    "max_cam_distance": 70,
    "start_buffer_frames": 45,
    "end_buffer_frames": 70
  },
  "drivers": ["NOR", "VER"]
}


(for my later reference):

use fake-bpy-module-latest for type hints and language server support for blender bpy and bmesh
