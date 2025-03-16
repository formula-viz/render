import math

from py.render.data_funcs.load_driver_data import (
    load_from_fastf1,
    process_grouped_driver_tels,
)
from tests.bases import SetupAlpha


class TestStartFinishSyncOfSmoothedDF(SetupAlpha):
    def test_start_sync(self):
        driver_dfs = self.driver_dfs
        all_start_points: list[tuple[float, float, float]] = []

        for _, df in driver_dfs.items():
            x_points = df["X"].astype(float)
            y_points = df["Y"].astype(float)
            z_points = df["Z"].astype(float)

            start_buffer_frames = self.config["render"]["start_buffer_frames"]
            start_point = (
                x_points[start_buffer_frames],
                y_points[start_buffer_frames],
                z_points[start_buffer_frames],
            )
            all_start_points.append(start_point)

        max_difference = 0.15  # 0.15 should be visually irrecognizable

        for i in range(len(all_start_points)):
            cur_start = all_start_points[i]
            for j in range(i + 1, len(all_start_points)):
                next_start = all_start_points[j]
                distance = math.sqrt(
                    (cur_start[0] - next_start[0]) ** 2
                    + (cur_start[1] - next_start[1]) ** 2
                    + (cur_start[2] - next_start[2]) ** 2
                )
                self.assertLess(distance, max_difference)


class TestStartFinishSyncOfInitialTel(SetupAlpha):
    def test_start_finish_sync(self):
        driver_tels = load_from_fastf1(self.config["year"], self.config["track"])
        _ = process_grouped_driver_tels(
            driver_tels, self.track_data.inner_points, self.track_data.outer_points
        )

        # this should adjust the driver tels so that the start and end points are the closest
        # points in that set of points to the line, so there could be some variance
        # but it should be minimal

        all_start_points: list[tuple[float, float, float]] = []
        all_end_points: list[tuple[float, float, float]] = []

        for _, tel in driver_tels.items():
            x_points = tel["X"].astype(float)
            y_points = tel["Y"].astype(float)
            z_points = tel["Z"].astype(float)

            # Assert there are no NaN or null values in the coordinates
            assert x_points.notna().all(), "X coordinates contain NaN/null values"  # pyright: ignore
            assert y_points.notna().all(), "Y coordinates contain NaN/null values"  # pyright: ignore
            assert z_points.notna().all(), "Z coordinates contain NaN/null values"  # pyright: ignore

            start_point = (x_points.iloc[0], y_points.iloc[0], z_points.iloc[0])
            end_point = (x_points.iloc[-1], y_points.iloc[-1], z_points.iloc[-1])

            all_start_points.append(start_point)
            all_end_points.append(end_point)

        first_val = all_start_points[0]
        for start_point in all_start_points:
            assert start_point == first_val

        first_val = all_end_points[0]
        for end_point in all_end_points:
            assert end_point == first_val
