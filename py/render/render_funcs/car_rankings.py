import numpy as np

def point_to_line_distance(point, line_start, line_end):
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
        return np.linalg.norm(point - line_start)
    # If projection falls after end of line segment
    if projection_length > line_length:
        return np.linalg.norm(point - line_end)

    projection = line_start + line_vec * projection_length
    return np.linalg.norm(point - projection)


def rank_closeness(track_data, track_idx, driver_idx, driver_dfs):
    inner_point = track_data.inner_points[track_idx]
    outer_point = track_data.outer_points[track_idx]

    driver_rank = {}

    # for each driver, calculate the distance to the line created by the inner and outer points
    for driver, df in driver_dfs.items():
        point = np.array([df["X"][driver_idx], df["Y"][driver_idx], df["Z"][driver_idx]])
        distance = point_to_line_distance(point, inner_point, outer_point)
        driver_rank[driver] = distance

    # sort the drivers by distance
    sorted_drivers = sorted(driver_rank.items(), key=lambda x: x[1])
    return sorted_drivers


# the previous_reference_idx is the line from which the previous
# frame's ranking was calculated
def find_closest_track_idx(inner_points, outer_points, previous_reference_idx, car_point):
    assert len(inner_points) == len(outer_points), "Inner and outer points must have the same length"
    n = len(inner_points)

    def next_pos(idx):
        return (idx + 1) % n

    def next_neg(idx):
        return (idx - 1) % n

    pos = previous_reference_idx
    neg = next_neg(previous_reference_idx)

    pos_distance = point_to_line_distance(car_point, inner_points[pos], outer_points[pos])
    neg_distance = point_to_line_distance(car_point, inner_points[neg], outer_points[neg])

    while point_to_line_distance(car_point, inner_points[next_pos(pos)], outer_points[next_pos(pos)]) < pos_distance:
        pos = next_pos(pos)
        pos_distance = point_to_line_distance(car_point, inner_points[pos], outer_points[pos])

    while point_to_line_distance(car_point, inner_points[next_neg(neg)], outer_points[next_neg(neg)]) < neg_distance:
        neg = next_neg(neg)
        neg_distance = point_to_line_distance(car_point, inner_points[neg], outer_points[neg])

    return pos if pos_distance < neg_distance else neg

# based on the track data, start finish line idx which references
# an index of the points in track_data and the driver_dfs which
# indicates the positions of the cars, we should be able to rank the
# positions of the cars at each frame or index of track_data by
# calculating distance to t        self.original_level = logging.root.levelhe line created by each vertex of track_data
def main(track_data, start_finish_line_idx, driver_dfs, config):
    start_buffer_frames = config["render"]["start_buffer_frames"]
    end_buffer_frames = config["render"]["end_buffer_frames"]

    print(len(driver_dfs["NOR"]["X"]) - end_buffer_frames - start_buffer_frames)
    print(len(track_data.inner_points))

    track_idx = start_finish_line_idx
    for i in range(start_buffer_frames, len(driver_dfs["NOR"]["X"]) - end_buffer_frames):
        sorted_drivers = rank_closeness(track_data, track_idx%len(track_data.inner_points), i, driver_dfs)
        track_idx -= 1
        print(f"Frame {i} winner: {sorted_drivers[0][0]}, distance: {sorted_drivers[0][1]}")
