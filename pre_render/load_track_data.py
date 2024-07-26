import csv
import os

import numpy as np
import pandas as pd
import requests
from scipy.interpolate import splev, splprep


def load_raw_data(year: int, track: str, use_latest_year: bool = True):
    # the current year may not be available, if it isn't, check if use_latest_year, then get the latest year
    track_csv_url = f"https://raw.githubusercontent.com/formula-viz/track-data-collection-gui-app/main/track_data/{year}_{track}.csv"
    response = requests.get(
        track_csv_url, auth=("quinn-caverly", "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"), verify=False
    )

    down_year = year
    while response.status_code != 200 and use_latest_year and down_year > 2000:
        down_year -= 1
        track_csv_url = f"https://raw.githubusercontent.com/formula-viz/track-data-collection-gui-app/main/track_data/{down_year}_{track}.csv"
        response = requests.get(
            track_csv_url, auth=("quinn-caverly", "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"), verify=False
        )

    response.raise_for_status()
    reader = csv.DictReader(response.text.splitlines())

    left_x = []
    left_y = []
    left_z = []

    right_x = []
    right_y = []
    right_z = []
    for row in reader:
        left_x.append(float(row["left_X"]))
        left_y.append(float(row["left_Y"]))
        left_z.append(float(row["left_Z"]))

        right_x.append(float(row["right_X"]))
        right_y.append(float(row["right_Y"]))
        right_z.append(float(row["right_Z"]))

    track_edges = pd.DataFrame(
        {
            "left_X": left_x,
            "left_Y": left_y,
            "left_Z": left_z,
            "right_X": right_x,
            "right_Y": right_y,
            "right_Z": right_z,
        }
    )

    return track_edges


def smooth_points(track_points: pd.DataFrame):
    lefts = np.array(track_points[["lefts_X", "lefts_Y", "lefts_Z"]])
    rights = np.array(track_points[["rights_X", "rights_Y", "rights_Z"]])

    # we need to add the first point to the end of both to close the loop
    # lefts = np.append(lefts, [lefts[0]], axis=0)
    # rights = np.append(rights, [rights[0]], axis=0)

    num_new_points = 2000

    def smooth_edge(points, num_new_points):
        x = points[:, 0]
        y = points[:, 1]

        tck, _ = splprep([x, y], s=100)  # Increase s to make the curve smoother
        unew = np.linspace(0, 1.0, num_new_points)
        out = splev(unew, tck)

        new_points_2d = []
        for i in range(len(out[0])):
            new_points_2d.append((out[0][i], out[1][i]))

        return new_points_2d

    new_lefts_2d = smooth_edge(lefts, num_new_points)
    new_rights_2d = smooth_edge(rights, num_new_points)

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

    new_lefts_z = linearly_interpolate_z_vals(lefts[:, 2], num_new_points)
    new_rights_z = linearly_interpolate_z_vals(rights[:, 2], num_new_points)

    left_x = []
    left_y = []
    left_z = []

    right_x = []
    right_y = []
    right_z = []

    for i in range(num_new_points):
        left_x.append(new_lefts_2d[i][0])
        left_y.append(new_lefts_2d[i][1])
        left_z.append(new_lefts_z[i])

        right_x.append(new_rights_2d[i][0])
        right_y.append(new_rights_2d[i][1])
        right_z.append(new_rights_z[i])

    new_track_points = pd.DataFrame(
        {
            "left_X": left_x,
            "left_Y": left_y,
            "left_Z": left_z,
            "right_X": right_x,
            "right_Y": right_y,
            "right_Z": right_z,
        }
    )

    return new_track_points


# the idea is that we get just left and right points from the previous api,
# this is because the car could go clockwise or counter clockwise around the track,
# which is otuer or inner is not given, so we just use some math to calculate which is which
def assign_inner_outer(track_points):
    # grab inner points, the 0th index of each tuple of track_points
    lefts = [(row["left_X"], row["left_Y"], row["left_Z"]) for _, row in track_points.iterrows()]
    rights = [(row["right_X"], row["right_Y"], row["right_Z"]) for _, row in track_points.iterrows()]

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

    # we want to make a new track_points of inner_X, inner_Y, inner_Z, outer_X, outer_Y, outer_Z
    inner_x = [point[0] for point in inner_points]
    inner_y = [point[1] for point in inner_points]
    inner_z = [point[2] for point in inner_points]

    outer_x = [point[0] for point in outer_points]
    outer_y = [point[1] for point in outer_points]
    outer_z = [point[2] for point in outer_points]

    new_track_points = pd.DataFrame(
        {
            "inner_X": inner_x,
            "inner_Y": inner_y,
            "inner_Z": inner_z,
            "outer_X": outer_x,
            "outer_Y": outer_y,
            "outer_Z": outer_z,
        }
    )

    return new_track_points, inner_points, outer_points


# the idea is to take the track_points which have already been modified and interpolated
# then, we add lines which are adjacent to the inner and outer points so that it creates the appearance of a curb
# then, in blender we can add faces between the outer edge and the outer curb line for example to create the outer curb
def add_curbs(inner_points, outer_points):
    # the default track width is 12 meters
    curb_width = 2

    inner_curb = curb(inner_points, outer_points, curb_width)
    outer_curb = curb(outer_points, inner_points, curb_width)

    inner_curb_x = [point[0] for point in inner_curb]
    inner_curb_y = [point[1] for point in inner_curb]
    inner_curb_z = [point[2] for point in inner_curb]

    outer_curb_x = [point[0] for point in outer_curb]
    outer_curb_y = [point[1] for point in outer_curb]
    outer_curb_z = [point[2] for point in outer_curb]

    curbs = pd.DataFrame(
        {
            "inner_curb_X": inner_curb_x,
            "inner_curb_Y": inner_curb_y,
            "inner_curb_Z": inner_curb_z,
            "outer_curb_X": outer_curb_x,
            "outer_curb_Y": outer_curb_y,
            "outer_curb_Z": outer_curb_z,
        }
    )

    return curbs


def curb(cur, other, curb_width):
    # take the line which is perpendicular to the cur inner_point and the next inner_point
    # then, go curb_width along that line, away from the current outer_point

    curb = []
    for i in range(len(cur)):
        next_idx = i + 1
        if next_idx >= len(cur):
            next_idx = 0

        cur_vec = (cur[next_idx][0] - cur[i][0], cur[next_idx][1] - cur[i][1])
        perp_vec = (cur_vec[1], -cur_vec[0])
        mag = (perp_vec[0] ** 2 + perp_vec[1] ** 2) ** 0.5
        unit_perp_vec = (perp_vec[0] / mag, perp_vec[1] / mag)

        curb_vec = (unit_perp_vec[0] * curb_width, unit_perp_vec[1] * curb_width)
        # in order to get the correct curb point, we both subtract and add the curb_vec
        # then, we find the one which is further from the other point

        curb_point_a = (cur[i][0] - curb_vec[0], cur[i][1] - curb_vec[1])
        curb_point_b = (cur[i][0] + curb_vec[0], cur[i][1] + curb_vec[1])

        if i == 0:
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

        # TODO, this code shouldn't be necessary, I don't know why in certain situations the curb is jumping over
        # granted, this code will work but this function could be more elegant
        # if i is not 0, then we add the curb point which is closer to the previous curb point
        else:
            prev_curb_point = curb[i - 1]

            dist_a = (prev_curb_point[0] - curb_point_a[0]) ** 2 + (prev_curb_point[1] - curb_point_a[1]) ** 2
            dist_b = (prev_curb_point[0] - curb_point_b[0]) ** 2 + (prev_curb_point[1] - curb_point_b[1]) ** 2

            if dist_a < dist_b:
                curb_point_a = (curb_point_a[0], curb_point_a[1], cur[i][2])
                curb.append(curb_point_a)
            else:
                curb_point_b = (curb_point_b[0], curb_point_b[1], cur[i][2])
                curb.append(curb_point_b)

    assert len(curb) == len(cur)
    return curb


def save_to_csv(track_points: pd.DataFrame, curb_points: pd.DataFrame, year: str, track: str):
    loc = f"data/track_data/{year}_{track}.csv"
    new = track_points.join(curb_points)
    new.to_csv(loc, index=False)


def already_done(year: str, track: str):
    loc = f"data/track_data/{year}_{track}.csv"
    if os.path.exists(loc):
        df = pd.read_csv(loc)
        return True, df
    return False, None


def main(year: int, track: str, use_latest_year: bool = True) -> pd.DataFrame:
    is_done, df = already_done(str(year), track)
    if is_done:
        print("Already fetched this track data, skipping...")
        return df

    print("Fetching and processing track data")

    track_edges = load_raw_data(year, track, use_latest_year)
    track_edges = smooth_points(track_edges)

    track_edges, inner_points, outer_points = assign_inner_outer(track_edges)
    curbs = add_curbs(inner_points, outer_points)
    save_to_csv(track_edges, curbs, str(year), track)

    print("Done processing track data")
    return track_edges
