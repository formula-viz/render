"""Calculate car ranking.

For each frame in the video, return a list of tuples containing the driver and their distance to the reference line.
"""

import numpy as np
import pandas as pd
from numpy._typing import NDArray

from py.utils.config import Config
from py.utils.models import Driver


def point_to_line_distance(
    point: NDArray[np.float64],
    line_start: NDArray[np.float64],
    line_end: NDArray[np.float64],
) -> float:
    """Calculate the distance from a point to a line segment."""
    point = np.array(point)
    line_start = np.array(line_start)
    line_end = np.array(line_end)

    line_vec = line_end - line_start
    line_length = np.linalg.norm(line_vec)

    line_vec = line_vec / line_length
    point_vec = point - line_start
    projection_length = np.dot(point_vec, line_vec)

    # If projection falls before beginning of line segment
    if projection_length < 0:
        return float(np.linalg.norm(point - line_start))
    # If projection falls after end of line segment
    if projection_length > line_length:
        return float(np.linalg.norm(point - line_end))

    projection = line_start + line_vec * projection_length
    return float(np.linalg.norm(point - projection))


def find_closest_track_idx(
    inner_points, outer_points, previous_reference_idx, car_point
) -> int:
    """Find the closest track segment to a car point.

    This function searches for the track segment closest to the car point,
    starting from the previous reference index. It searches in both positive
    and negative directions along the track.

    Args:
        inner_points: List of inner track boundary points
        outer_points: List of outer track boundary points
        previous_reference_idx: The index of the line from which the previous
            frame's ranking was calculated
        car_point: The position of the car

    Returns:
        The index of the closest track segment to the car point

    """
    assert len(inner_points) == len(outer_points), (
        "Inner and outer points must have the same length"
    )
    n = len(inner_points)

    def next_pos(idx):
        return (idx + 1) % n

    def next_neg(idx):
        return (idx - 1) % n

    pos = previous_reference_idx
    neg = next_neg(previous_reference_idx)

    pos_distance = point_to_line_distance(
        car_point, inner_points[pos], outer_points[pos]
    )
    neg_distance = point_to_line_distance(
        car_point, inner_points[neg], outer_points[neg]
    )

    while (
        point_to_line_distance(
            car_point, inner_points[next_pos(pos)], outer_points[next_pos(pos)]
        )
        < pos_distance
    ):
        pos = next_pos(pos)
        pos_distance = point_to_line_distance(
            car_point, inner_points[pos], outer_points[pos]
        )

    # only do one less for neg
    if (
        point_to_line_distance(
            car_point, inner_points[next_neg(neg)], outer_points[next_neg(neg)]
        )
        < neg_distance
    ):
        neg = next_neg(neg)
        neg_distance = point_to_line_distance(
            car_point, inner_points[neg], outer_points[neg]
        )

    return pos if pos_distance < neg_distance else neg


def find_most_distant_closest_point(
    inner_points: list[NDArray[np.float64]],
    outer_points: list[NDArray[np.float64]],
    previous_reference_idx: int,
    car_points: list[NDArray[np.float64]],
):
    """Find the point which is furthest from the previous line which was used to calculate the ranking.

    This will allow us to find the next reference line.
    """
    closest_idxs = [
        find_closest_track_idx(
            inner_points, outer_points, previous_reference_idx, car_point
        )
        for car_point in car_points
    ]

    cur_farthest_point_idx = 0
    for idx in closest_idxs:
        cur_farthest_point_idx = max(cur_farthest_point_idx, idx)

    # now, we have the farthest point idx, we want to check if the car is actually
    # the car might not actually be infront of this point, we should be able to just add 1 to the idx
    # track points are close enough together that this should not cause bugs
    return (cur_farthest_point_idx + 1) % len(inner_points)


# the frame here is implicit. All of the car points will be different cars at the same frame
def ranking_at_frame(
    inner_points: list[NDArray[np.float64]],
    outer_points: list[NDArray[np.float64]],
    previous_reference_idx: int,
    car_points: list[NDArray[np.float64]],
) -> tuple[list[tuple[int, float]], int]:
    """Calculate car ranking at one frame."""
    new_reference_idx = find_most_distant_closest_point(
        inner_points, outer_points, previous_reference_idx, car_points
    )
    # for each driver, we calculate their distance to the new reference line

    drivers: list[tuple[int, float]] = []
    for driver_idx in range(len(car_points)):
        distance = float(
            point_to_line_distance(
                car_points[driver_idx],
                inner_points[new_reference_idx],
                outer_points[new_reference_idx],
            )
        )
        drivers.append((driver_idx, distance))

    return (sorted(drivers, key=lambda x: x[1]), new_reference_idx)


def main(
    track_data: pd.DataFrame,
    start_finish_line_idx: int,
    driver_dfs: dict[Driver, pd.DataFrame],
    config: Config,
    focused_driver: Driver,
) -> list[list[tuple[Driver, float]]]:
    """Caclulate car ranking.

    For each frame in the video, return a list of tuples containing the driver and their distance to the reference line.
    """
    start_buffer_frames = config["render"]["start_buffer_frames"]
    end_buffer_frames = config["render"]["end_buffer_frames"]

    inner_points = [np.array(p) for p in track_data.inner_points]
    outer_points = [np.array(p) for p in track_data.outer_points]

    indices: dict[int, Driver] = {}
    driver_data = []
    for i, (driver, df) in enumerate(driver_dfs.items()):
        car_points = [
            np.array([df["X"][i], df["Y"][i], df["Z"][i]]) for i in range(len(df["X"]))
        ]
        driver_data.append(car_points)
        indices[i] = driver

    final_rank: list[list[tuple[Driver, float]]] = []
    reference_idx = start_finish_line_idx
    for i in range(
        start_buffer_frames, len(driver_dfs[focused_driver]) - end_buffer_frames
    ):
        current_frame_positions = [driver_points[i] for driver_points in driver_data]

        rankings, reference_idx = ranking_at_frame(
            inner_points, outer_points, reference_idx, current_frame_positions
        )

        final_rank.append([(indices[rank[0]], rank[1]) for rank in rankings])

    return final_rank
