import unittest
import numpy as np

from py.render.render_funcs.car_rankings import (
    point_to_line_distance,
    find_closest_track_idx,
    find_most_distant_closest_point,
    ranking_at_frame,
)
from tests.bases import SetupAlpha


class TestPointToLineDistance(unittest.TestCase):
    def test_two_points(self):
        point_a = np.array([5, 0, 0])
        point_b = np.array([10, 0, 0])

        line_start = np.array([0, -5, 0])
        line_end = np.array([0, 5, 0])

        distance_a = point_to_line_distance(point_a, line_start, line_end)
        distance_b = point_to_line_distance(point_b, line_start, line_end)

        self.assertAlmostEqual(float(distance_a), 5.0)
        self.assertAlmostEqual(float(distance_b), 10.0)

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


class TestFindMostDistantClosestPoint(SetupAlpha):
    def test_3_cars(self):
        inner_points = [np.array(p) for p in [(0, 0, 0), (1, 0, 0), (2, 0, 0), (3, 0, 0)]]
        outer_points = [np.array(p) for p in [(0, 1, 0), (1, 1, 0), (2, 1, 0), (3, 1, 0)]]
        car_points = [np.array(p) for p in [(1, 0.5, 0), (0, 0.5, 0), (0, 0.5, 0)]]
        # if the previous reference point is 0, then the closest points are 1, 0, 0
        # and the point index 1 is furthest from the line so it should be chosen
        # then 1 is added, the new reference line is idx 2

        closest_idx = find_most_distant_closest_point(inner_points, outer_points, 0, car_points)
        self.assertEqual(closest_idx, 2)

        # say ref point is now 2, the closest is still 1, we should get 2 again
        car_points = [np.array(p) for p in [(1, 0.5, 0), (1, 0.5, 0), (1, 0.5, 0)]]
        closest_idx = find_most_distant_closest_point(inner_points, outer_points, 2, car_points)
        self.assertEqual(closest_idx, 2)

        # now move the cars up to the next, next line, now we should get 3
        car_points = [np.array(p) for p in [(3, 0.8, 0), (3, 0.2, 0), (3, 0.7, 0)]]
        closest_idx = find_most_distant_closest_point(inner_points, outer_points, 2, car_points)
        # closest is 3 but we add 1, swinging back to the beginning
        self.assertEqual(closest_idx, 0)


class TestRankingAtFrame(SetupAlpha):
    def test_3_cars(self):
        inner_points = [np.array(p) for p in [(0, 0, 0), (1, 0, 0), (2, 0, 0), (3, 0, 0)]]
        outer_points = [np.array(p) for p in [(0, 1, 0), (1, 1, 0), (2, 1, 0), (3, 1, 0)]]
        car_points = [np.array(p) for p in [(1, 0.5, 0), (0, 0.5, 0), (0, 0.5, 0)]]

        # we know that the reference point will be index 2, so the rank should be
        # either 0, 1, 2 or 0, 2, 1
        rank = ranking_at_frame(inner_points, outer_points, 0, car_points)
        rank_indices = [driver_idx for driver_idx, _ in rank[0]]
        self.assertIn(rank_indices, [[0, 1, 2], [0, 2, 1]])

        # now reshuffle the car points
        car_points = [np.array(p) for p in [(1, 0.5, 0), (2, 0.5, 0), (0, 0.5, 0)]]
        rank = ranking_at_frame(inner_points, outer_points, 1, car_points)
        rank_indices = [driver_idx for driver_idx, _ in rank[0]]
        self.assertEqual(rank_indices, [1, 0, 2])
