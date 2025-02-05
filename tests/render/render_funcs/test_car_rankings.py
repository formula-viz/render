import unittest
import numpy as np

from py.render.render_funcs.car_rankings import point_to_line_distance, rank_closeness, find_closest_track_idx
from tests.bases import SetupAlpha

class TestPointToLineDistance(unittest.TestCase):
    def test_two_points(self):
        point_a = np.array([5, 0, 0])
        point_b = np.array([10, 0, 0])

        line_start = np.array([0, -5, 0])
        line_end = np.array([0, 5, 0])

        distance_a = point_to_line_distance(point_a, line_start, line_end)
        distance_b = point_to_line_distance(point_b, line_start, line_end)

        self.assertAlmostEqual(distance_a, 5.0)
        self.assertAlmostEqual(distance_b, 10.0)

    def test_equal_points(self):
        point_a = np.array([5, 0, 0])
        point_b = np.array([5, 0, 0])

        line_start = np.array([0, -5, 0])
        line_end = np.array([0, 5, 0])

        distance_a = point_to_line_distance(point_a, line_start, line_end)
        distance_b = point_to_line_distance(point_b, line_start, line_end)

        self.assertAlmostEqual(distance_a, distance_b)

class TestFindClosestTrackIdx(SetupAlpha):
    def test_next_ahead(self):
        inner_points = [(0, 0, 0), (1, 0, 0), (2, 0, 0)]
        outer_points = [(0, 1, 0), (1, 1, 0), (2, 1, 0)]

        point = np.array([1, 0.5, 0])

        closest_idx = find_closest_track_idx(inner_points, outer_points, 0, point)
        self.assertEqual(closest_idx, 1)

    def test_next_behind(self):
        inner_points = [(0, 0, 0), (1, 0, 0), (2, 0, 0)]
        outer_points = [(0, 1, 0), (1, 1, 0), (2, 1, 0)]

        point = np.array([1, 0.5, 0])

        closest_idx = find_closest_track_idx(inner_points, outer_points, 2, point)
        self.assertEqual(closest_idx, 1)

    def test_end_edge(self):
        inner_points = [(3, 0, 0), (1, 0, 0), (2, 0, 0)]
        outer_points = [(3, 1, 0), (1, 1, 0), (2, 1, 0)]

        point = np.array([3, 0.5, 0])

        closest_idx = find_closest_track_idx(inner_points, outer_points, 2, point)
        self.assertEqual(closest_idx, 0)

    def test_beginning_edge(self):
        inner_points = [(3, 0, 0), (1, 0, 0), (2, 0, 0)]
        outer_points = [(3, 1, 0), (1, 1, 0), (2, 1, 0)]

        point = np.array([2, 0.5, 0])

        closest_idx = find_closest_track_idx(inner_points, outer_points, 0, point)
        self.assertEqual(closest_idx, 2)
