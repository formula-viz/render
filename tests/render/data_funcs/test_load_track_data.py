import math

from tests.bases import SetupAlpha


class TestLoadTrackData(SetupAlpha):
    def test_no_outliers(self):
        inner_points = self.track_data.inner_points
        outer_points = self.track_data.outer_points

        prev_inner_point = None
        for i, inner_point in enumerate(inner_points):
            if prev_inner_point:
                distance = math.sqrt(
                    (prev_inner_point[0] - inner_point[0]) ** 2
                    + (prev_inner_point[1] - inner_point[1]) ** 2
                )
                assert distance < 1.0, (
                    f"Distance between inner points {i} and {i + 1} out of {len(inner_points)} is {distance}"
                )
            prev_inner_point = inner_point

        prev_outer_point = None
        for i, outer_point in enumerate(outer_points):
            if prev_outer_point:
                distance = math.sqrt(
                    (prev_outer_point[0] - outer_point[0]) ** 2
                    + (prev_outer_point[1] - outer_point[1]) ** 2
                )
                assert distance < 1.0, (
                    f"Distance between outer points {i} and {i + 1} out of {len(outer_points)} is {distance}"
                )
            prev_outer_point = outer_point
