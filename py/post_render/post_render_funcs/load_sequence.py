import os

import bpy
from py.utils.project_structure import FRAMES_DIR


def main():
    bpy.context.scene.sequence_editor_create()

    bpy.context.scene.render.use_sequencer = True
    file_paths = sorted([f for f in os.listdir(FRAMES_DIR)])

    for i, file_path in enumerate(file_paths):
        bpy.data.scenes[0].sequence_editor.sequences.new_image(
            name=f"Image{i+1}",
            filepath=os.path.join(FRAMES_DIR, file_path),
            channel=2,
            frame_start=i + 1,
            fit_method="ORIGINAL",
        )

    return len(file_paths)
