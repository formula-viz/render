import os

import numpy as np
import pandas as pd
from scipy.interpolate import splev, splprep
from utils.project_structure import TrackData


# in the earlier bash script, we clone the repository locally
def load_raw_data(year: int, track: str, use_latest_year: bool = True):
    track_data_dir = TrackData.get_track_data_dir()
    # iterate through contents of track_data, finding all files containing track
    # then, we find the file with the latest year
    # if use_latest_year is false, we use the year given
    track_data_files = os.listdir(track_data_dir)
    track_data_files = [file for file in track_data_files if track in file]

    if not track_data_files:
        raise FileNotFoundError(f"Track data not found for {track}")

    if use_latest_year:
        latest_year = 0
        latest_file = ""
        for file in track_data_files:
            year = TrackData.get_year_of_track_file(file)
            if int(year) > latest_year:
                latest_year = int(year)
                latest_file = file
        track_data_file = latest_file
    else:
        track_data_file = TrackData.get_track_file(str(year), track)

        if track_data_file not in track_data_files:
            raise FileNotFoundError(f"Track data not found for {track} in {year}, use_latest_year is set to False")

    track_data_path = os.path.join(track_data_dir, track_data_file)
    track_data = pd.read_csv(track_data_path)

    return track_data


# this function may be useful if I ever transition to using the 3d data
def linearly_interpolate_z_vals(z_vals, num_new_points):
    # we want to interpolate the z values, not smooth them
    # for now, the z value's will be the same for the inner and outer points
    # we stretch z values to fit num_new_points
    # if we have 1000 points and 2000 new points, we need to stretch the z values by 2
    stretch_val = num_new_points / len(z_vals)
    new_z_vals = np.zeros(num_new_points)

    for i, z_val in enumerate(z_vals):
        new_z_vals[int(i * stretch_val)] = z_val

    # if we have two values which are not 0 and say they are 20 apart, then we fill the vals between them linearly
    # if a is 10 and b is 20 and there are 3 spots between, we add 10.25, 10.5, 10.75

    # hold a pointer to the cur non-zero value in i, j is the next non zero value, then we step between them
    i = 0
    while new_z_vals[i] == 0:
        i += 1

    j = i + 1
    while j < len(new_z_vals):
        if new_z_vals[j] == 0:
            j += 1
            continue  # this should ensure that the loop doesnt break

        # now that we have i pointing to a and j to b, find the spaces between them
        num_spaces = j - i - 1  # if j = 3 and i = 0, then i 0 0 3, 2 spaces between = 3 - 0 - 1
        dif = new_z_vals[j] - new_z_vals[i]
        # if dif is 10 and num_spaces is 3, we add 10/4 to each space
        step = dif / (num_spaces + 1)

        for k in range(i + 1, j):
            new_z_vals[k] = new_z_vals[k - 1] + step

        # now we need to replace i with j and find the next non zero value
        i = j
        j += 1

    # now we need to interpolate between the last non zero value and the first non zero value
    # as it is, i is pointing to the last non zero value
    j = 0
    while new_z_vals[j] == 0:
        j += 1

    # now we have i pointing to the last non zero value and j to the first non zero value
    # now j is the smaller value, j might be 10 and i is 200, if there are 210 elems, then there are 9 + 11 = 20 spaces
    num_spaces = len(new_z_vals) - i - 1 + j
    dif = new_z_vals[j] - new_z_vals[i]
    step = dif / (num_spaces + 1)

    n = 1
    while n <= num_spaces:
        idx = (i + n) % len(new_z_vals)
        below_idx = (i + n - 1) % len(new_z_vals)
        new_z_vals[idx] = new_z_vals[below_idx] + step

        n += 1

    return new_z_vals


def smooth_points(track_points: pd.DataFrame):
    def smooth_closed_loop(points, num_points=10000, smoothing=100):
        # Ensure points is a numpy array
        points = np.asarray(points)

        # Separate x and y coordinates
        x, y = points.T

        # Fit a periodic spline
        tck, _ = splprep([x, y], s=smoothing, per=True)

        # Generate smooth points
        u_new = np.linspace(0, 1, num_points)
        smooth_x, smooth_y = splev(u_new, tck)

        return smooth_x, smooth_y

    lefts = np.array(track_points[["lefts_X", "lefts_Y"]])
    rights = np.array(track_points[["rights_X", "rights_Y"]])

    lefts = np.roll(lefts, len(lefts) // 2, axis=0)
    rights = np.roll(rights, len(rights) // 2, axis=0)

    lefts_x, lefts_y = smooth_closed_loop(lefts)
    # instead of generating a spline for both lefts and rights, we generate a spline for just the lefts
    # this is because around corners, the lines end up overlapping due to the fact that the
    # distances are shorter around the two curves, this way we can ensure that they do not
    # overlap and also make the width more constant around the track.
    rights_x, rights_y = [], []
    track_width = 12  # this is hardcoded from how we generate the track
    for i in range(len(lefts_x)):
        next_idx = i + 1 if i + 1 < len(lefts_x) else 0
        cur_point = (lefts_x[i], lefts_y[i])
        next_point = (lefts_x[next_idx], lefts_y[next_idx])

        vec = (next_point[0] - cur_point[0], next_point[1] - cur_point[1])
        mag = (vec[0] ** 2 + vec[1] ** 2) ** 0.5
        unit_vec = (vec[0] / mag, vec[1] / mag)

        perp_vec = (unit_vec[1], -unit_vec[0])
        # we go track width in each direction
        a = (cur_point[0] - perp_vec[0] * track_width, cur_point[1] - perp_vec[1] * track_width)
        b = (cur_point[0] + perp_vec[0] * track_width, cur_point[1] + perp_vec[1] * track_width)
        # how do we know which one to choose?
        # iterate through all rights points, as we are recreating the rights line, and find the shortest distance
        # between a and b, then choose the one which is further from the closest point
        min_dist_a = 1000
        min_dist_b = 1000
        for right in rights:
            dist_a = ((right[0] - a[0]) ** 2 + (right[1] - a[1]) ** 2) ** 0.5
            dist_b = ((right[0] - b[0]) ** 2 + (right[1] - b[1]) ** 2) ** 0.5
            if dist_a < min_dist_a:
                min_dist_a = dist_a
            if dist_b < min_dist_b:
                min_dist_b = dist_b

        if min_dist_a < min_dist_b:
            rights_x.append(a[0])
            rights_y.append(a[1])
        else:
            rights_x.append(b[0])
            rights_y.append(b[1])

    new_track_points = pd.DataFrame(
        {
            "lefts_X": lefts_x,
            "lefts_Y": lefts_y,
            "lefts_Z": np.zeros(len(lefts_x)),
            "rights_X": rights_x,
            "rights_Y": rights_y,
            "rights_Z": np.zeros(len(rights_x)),
        }
    )

    return new_track_points


# the idea is that we get just left and right points from the previous api,
# this is because the car could go clockwise or counter clockwise around the track,
# which is otuer or inner is not given, so we just use some math to calculate which is which
def assign_inner_outer(track_points):
    # grab inner points, the 0th index of each tuple of track_points
    lefts = [(row["lefts_X"], row["lefts_Y"], row["lefts_Z"]) for _, row in track_points.iterrows()]
    rights = [(row["rights_X"], row["rights_Y"], row["rights_Z"]) for _, row in track_points.iterrows()]

    # we want to assume the inner points as the shorter distnace, the outer points as the longer distance
    left_dist = 0
    right_dist = 0
    for i in range(len(lefts) - 1):
        left_dist += ((lefts[i][0] - lefts[i + 1][0]) ** 2 + (lefts[i][1] - lefts[i + 1][1]) ** 2) ** 0.5
        right_dist += ((rights[i][0] - rights[i + 1][0]) ** 2 + (rights[i][1] - rights[i + 1][1]) ** 2) ** 0.5

    if left_dist <= right_dist:
        outer_points = lefts
        inner_points = rights
    else:
        inner_points = rights
        outer_points = lefts

    return inner_points, outer_points


def curb(cur, other, curb_width):
    # take the line which is perpendicular to the cur inner_point and the next inner_point
    # then, go curb_width along that line, away from the current outer_point

    curb = []
    for i in range(len(cur)):
        next_idx = i + 1
        if next_idx == len(cur):
            # this ensures that they won't overlap, because they will be parallel at the end
            next_idx = i - 1

        cur_vec = (cur[next_idx][0] - cur[i][0], cur[next_idx][1] - cur[i][1])
        perp_vec = (cur_vec[1], -cur_vec[0])
        mag = (perp_vec[0] ** 2 + perp_vec[1] ** 2) ** 0.5
        unit_perp_vec = (perp_vec[0] / mag, perp_vec[1] / mag)

        curb_vec = (unit_perp_vec[0] * curb_width, unit_perp_vec[1] * curb_width)
        # in order to get the correct curb point, we both subtract and add the curb_vec
        # then, we find the one which is further from the other point

        curb_point_a = (cur[i][0] - curb_vec[0], cur[i][1] - curb_vec[1])
        curb_point_b = (cur[i][0] + curb_vec[0], cur[i][1] + curb_vec[1])

        other_point = other[i]

        dist_a = (other_point[0] - curb_point_a[0]) ** 2 + (other_point[1] - curb_point_a[1]) ** 2
        dist_b = (other_point[0] - curb_point_b[0]) ** 2 + (other_point[1] - curb_point_b[1]) ** 2

        if dist_a > dist_b:
            # we also need to add the z value of cur to the curb point
            curb_point_a = (curb_point_a[0], curb_point_a[1], cur[i][2])
            curb.append(curb_point_a)
        else:
            curb_point_b = (curb_point_b[0], curb_point_b[1], cur[i][2])
            curb.append(curb_point_b)

    assert len(curb) == len(cur)
    return curb


def main(year: int, track: str):
    print("Processing track data")
    use_latest_year = True  # this may cause problems if the track changes year to year
    track_edges = load_raw_data(year, track, use_latest_year)
    track_edges = smooth_points(track_edges)

    inner_points, outer_points = assign_inner_outer(track_edges)
    curb_width = 2
    inner_curb_points = curb(inner_points, outer_points, curb_width)
    outer_curb_points = curb(outer_points, inner_points, curb_width)

    print("Done processing track data")
    return (inner_points, outer_points, inner_curb_points, outer_curb_points)
