import unittest
import bpy

class TestBlenderFunctions(unittest.TestCase):
    def setUp(self):
        # Reset scene before each test
        bpy.ops.wm.read_factory_settings()

    def test_camera_position(self):
        bpy.ops.object.camera_add(location=(0, 0, 10))
        cam = bpy.context.active_object
        self.assertEqual(cam.location.z, 10)
        self.assertEqual(cam.location.x, 0)
        self.assertEqual(cam.location.y, 0)
