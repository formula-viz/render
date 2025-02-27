"""Tests for car ranking functionality in the rendering module.

This module tests various functions related to calculating car positions and rankings
on the track, including distance calculations, track index finding, and race position
determination.
"""

import unittest

import numpy as np

from py.render.render_funcs.car_rankings import (
    find_closest_track_idx,
    find_most_distant_closest_point,
    main,
    point_to_line_distance,
    ranking_at_frame,
)
from tests.bases import SetupAlpha


class TestPointToLineDistance(unittest.TestCase):
    """Tests for the point_to_line_distance function.

    Verifies that the function correctly calculates the perpendicular
    distance from a point to a line segment in 3D space.
    """

    def test_two_points(self):
        """Test distance calculation for two different points to the same line.

        Creates a vertical line and tests that points at different x-coordinates
        have the expected perpendicular distances to the line.
        """
        point_a = np.array([5, 0, 0])
        point_b = np.array([10, 0, 0])

        line_start = np.array([0, -5, 0])
        line_end = np.array([0, 5, 0])

        distance_a = point_to_line_distance(point_a, line_start, line_end)
        distance_b = point_to_line_distance(point_b, line_start, line_end)

        self.assertAlmostEqual(float(distance_a), 5.0)
        self.assertAlmostEqual(float(distance_b), 10.0)

    def test_equal_points(self):
        """Test that identical points return the same distance to a line.

        Verifies that the distance calculation is consistent when the same
        point is provided multiple times.
        """
        point_a = np.array([5, 0, 0])
        point_b = np.array([5, 0, 0])

        line_start = np.array([0, -5, 0])
        line_end = np.array([0, 5, 0])

        distance_a = point_to_line_distance(point_a, line_start, line_end)
        distance_b = point_to_line_distance(point_b, line_start, line_end)

        self.assertAlmostEqual(distance_a, distance_b)


class TestFindClosestTrackIdx(SetupAlpha):
    """Tests for the find_closest_track_idx function.

    Verifies that the function correctly identifies the closest track segment
    to a given point, considering the current reference index.
    """

    def test_next_ahead(self):
        """Test finding the closest track index when looking forward.

        Verifies that when starting from index 0, the function correctly
        identifies index 1 as closest to the test point.
        """
        inner_points = [(0, 0, 0), (1, 0, 0), (2, 0, 0)]
        outer_points = [(0, 1, 0), (1, 1, 0), (2, 1, 0)]

        point = np.array([1, 0.5, 0])

        closest_idx = find_closest_track_idx(inner_points, outer_points, 0, point)
        self.assertEqual(closest_idx, 1)

    def test_next_behind(self):
        """Test finding the closest track index when looking backward.

        Verifies that when starting from index 2, the function correctly
        identifies index 1 as closest to the test point.
        """
        inner_points = [(0, 0, 0), (1, 0, 0), (2, 0, 0)]
        outer_points = [(0, 1, 0), (1, 1, 0), (2, 1, 0)]

        point = np.array([1, 0.5, 0])

        closest_idx = find_closest_track_idx(inner_points, outer_points, 2, point)
        self.assertEqual(closest_idx, 1)

    def test_end_edge(self):
        """Test finding the closest track index at the end of the track.

        Verifies correct handling of edge cases when a point is closest to
        the first track segment when looking from near the end.
        """
        inner_points = [(3, 0, 0), (1, 0, 0), (2, 0, 0)]
        outer_points = [(3, 1, 0), (1, 1, 0), (2, 1, 0)]

        point = np.array([3, 0.5, 0])

        closest_idx = find_closest_track_idx(inner_points, outer_points, 2, point)
        self.assertEqual(closest_idx, 0)

    def test_beginning_edge(self):
        """Test finding the closest track index at the beginning of the track.

        Verifies correct handling of edge cases when a point is closest to
        the last track segment when looking from the beginning.
        """
        inner_points = [(3, 0, 0), (1, 0, 0), (2, 0, 0)]
        outer_points = [(3, 1, 0), (1, 1, 0), (2, 1, 0)]

        point = np.array([2, 0.5, 0])

        closest_idx = find_closest_track_idx(inner_points, outer_points, 0, point)
        self.assertEqual(closest_idx, 2)


class TestFindMostDistantClosestPoint(SetupAlpha):
    """Tests for the find_most_distant_closest_point function.

    Verifies that the function correctly identifies the most advanced car on the track
    by finding the furthest track segment that is closest to any car.
    """

    def test_3_cars(self):
        """Test finding the most distant point with three cars at various positions.

        Tests multiple scenarios with different car positions to ensure the
        function correctly identifies the most advanced track segment.
        """
        inner_points = [
            np.array(p) for p in [(0, 0, 0), (1, 0, 0), (2, 0, 0), (3, 0, 0)]
        ]
        outer_points = [
            np.array(p) for p in [(0, 1, 0), (1, 1, 0), (2, 1, 0), (3, 1, 0)]
        ]
        car_points = [np.array(p) for p in [(1, 0.5, 0), (0, 0.5, 0), (0, 0.5, 0)]]
        # if the previous reference point is 0, then the closest points are 1, 0, 0
        # and the point index 1 is furthest from the line so it should be chosen
        # then 1 is added, the new reference line is idx 2

        closest_idx = find_most_distant_closest_point(
            inner_points, outer_points, 0, car_points
        )
        self.assertEqual(closest_idx, 2)

        # say ref point is now 2, the closest is still 1, we should get 2 again
        car_points = [np.array(p) for p in [(1, 0.5, 0), (1, 0.5, 0), (1, 0.5, 0)]]
        closest_idx = find_most_distant_closest_point(
            inner_points, outer_points, 2, car_points
        )
        self.assertEqual(closest_idx, 2)

        # now move the cars up to the next, next line, now we should get 3
        car_points = [np.array(p) for p in [(3, 0.8, 0), (3, 0.2, 0), (3, 0.7, 0)]]
        closest_idx = find_most_distant_closest_point(
            inner_points, outer_points, 2, car_points
        )
        # closest is 3 but we add 1, swinging back to the beginning
        self.assertEqual(closest_idx, 0)

    def test_way_behind(self):
        """Test finding the most distant point when a car is significantly behind others.

        Verifies that the function correctly prioritizes cars that are ahead
        rather than being misled by cars that are far behind (which would be
        more distant from the previous reference line).
        """
        # create several points and some cars. 2 of the 3
        # cars will be 1 unit infront of the last point.
        # the other car will be far behind
        inner_points = [
            np.array(p)
            for p in [(0, 0, 0), (1, 0, 0), (2, 0, 0), (3, 0, 0), (4, 0, 0), (5, 0, 0)]
        ]
        outer_points = [
            np.array(p)
            for p in [(0, 1, 0), (1, 1, 0), (2, 1, 0), (3, 1, 0), (4, 1, 0), (5, 1, 0)]
        ]

        car_points = [np.array(p) for p in [(4, 0.5, 0), (4, 0.5, 0), (0, 0.5, 0)]]

        closest_idx = find_most_distant_closest_point(
            inner_points, outer_points, 3, car_points
        )
        # the next point should be 4 but we add 1, so we end up at index 5
        # a bug was occuring where it would take the car in last place because they were furthest
        # from the previous line, but we want the furthest ahead not furthest
        self.assertEqual(closest_idx, 5)


class TestRankingAtFrame(SetupAlpha):
    """Tests for the ranking_at_frame function.

    Verifies that the function correctly ranks cars based on their positions
    relative to track segments.
    """

    def test_3_cars(self):
        """Test car ranking with three cars at different positions.

        Tests that cars are correctly ranked based on their proximity to
        track segments, with appropriate handling of ambiguous cases.
        """
        inner_points = [
            np.array(p) for p in [(0, 0, 0), (1, 0, 0), (2, 0, 0), (3, 0, 0)]
        ]
        outer_points = [
            np.array(p) for p in [(0, 1, 0), (1, 1, 0), (2, 1, 0), (3, 1, 0)]
        ]
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


class TestCarRankingsMain(SetupAlpha):
    """Tests for the main car rankings function.

    Verifies that the main function correctly determines car positions
    throughout a race using real track and driver data.
    """

    def test_positions(self):
        """Test car positions at various frames throughout a race.

        Uses real race data to verify that car rankings are calculated
        correctly at multiple key moments, checking first, second, and
        last positions at different timestamps.
        """
        assert 2 == 3

        track_data = self.track_data
        driver_dfs = self.driver_dfs
        start_finish_line_idx = self.start_finish_line_idx
        config = self.config
        focused_driver = "NOR"

        rankings = main(
            track_data, start_finish_line_idx, driver_dfs, config, focused_driver
        )

        start_buffer_frames = config["render"]["start_buffer_frames"]
        # rankings returns starting at the actual start of the race not video

        def get_first(abs_frame):
            return rankings[abs_frame - start_buffer_frames][0][0]

        def get_second(abs_frame):
            return rankings[abs_frame - start_buffer_frames][1][0]

        def get_last(abs_frame):
            return rankings[abs_frame - start_buffer_frames][-1][0]

        self.assertEqual(get_first(84), "NOR")
        self.assertEqual(get_first(104), "NOR")
        self.assertEqual(get_first(212), "MAG")
        self.assertEqual(get_first(394), "ALO")

        self.assertEqual(get_first(411), "ALO")
        self.assertEqual(get_second(411), "HUL")

        self.assertEqual(get_last(687), "ZHO")
        self.assertEqual(get_first(687), "ALO")

        self.assertEqual(get_last(967), "GAS")

        self.assertEqual(get_first(1055), "COL")

        self.assertEqual(get_first(1175), "ALO")
        self.assertEqual(get_last(1175), "GAS")

        self.assertEqual(get_first(1530), "VER")
        self.assertEqual(get_last(1530), "ZHO")

        for i in range(2100, len(rankings)):
            self.assertEqual(get_first(i), "NOR")
