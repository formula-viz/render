"""Test suite for Blender integration and functionality verification."""

import unittest

import bpy


class TestBlenderFunctions(unittest.TestCase):
    """Test suite for Blender functionality verification."""

    def setUp(self):
        """Reset the Blender scene to factory settings before each test."""
        bpy.ops.wm.read_factory_settings()

    def test_camera_position(self):
        """Test that camera is correctly positioned at the specified coordinates."""
        bpy.ops.object.camera_add(location=(0, 0, 10))
        cam = bpy.context.active_object
        if cam is not None:
            self.assertEqual(cam.location.z, 10)
            self.assertEqual(cam.location.x, 0)
            self.assertEqual(cam.location.y, 0)
        else:
            self.fail("Failed to create camera object")
