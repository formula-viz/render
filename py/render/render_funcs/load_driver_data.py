import concurrent.futures
import json
import os
from concurrent.futures import ThreadPoolExecutor

import fastf1 as ff1
import mathutils
import numpy as np
import pandas as pd
import requests
from fastf1.core import Laps, Telemetry
from scipy.interpolate import UnivariateSpline
from utils.project_structure import DriverDataPS


def load_driver_headshots(driver_abbrevs, headshot_urls):
    # taking before .transform gives the original image
    headshot_urls = [url.split(".transform")[0] for url in headshot_urls]

    downloaded_count = 0
    for driver, url in zip(driver_abbrevs, headshot_urls):
        image_path = DriverDataPS.get_driver_image_path(driver)

        if not os.path.exists(image_path):
            try:
                response = requests.get(url)
                response.raise_for_status()

                with open(image_path, "wb") as image_file:
                    image_file.write(response.content)
                    downloaded_count += 1
            except requests.exceptions.RequestException as e:
                print(f"Failed to download image for driver {driver}: {e}")

    if downloaded_count > 0:
        print(f"Downloaded {downloaded_count} driver headshots")


def save_driver_times(driver_times: dict[str, str], year: str, track: str):
    loc = DriverDataPS.get_driver_times_path(year, track)
    with open(loc, "w") as file:
        json.dump(driver_times, file)


# this will only need to be called once for a particular year and track
# grab all drivers, then immediately process the data, do this in a batch
# so that the drives can be normalized with respect to each other
def load_from_fastf1(year: int, track: str):
    session = ff1.get_session(year, track, "Q")
    session.load()

    drivers = session.drivers
    drivers = [session.get_driver(d) for d in drivers]
    driver_abbrevs: list[str] = [d["Abbreviation"] for d in drivers]

    # let's load the driver images if they are not present already
    headshot_urls = [d["HeadshotUrl"] for d in drivers]
    load_driver_headshots(driver_abbrevs, headshot_urls)

    laps = session.laps

    def process_tel(q: Laps, driver: str):
        try:
            tel: Telemetry = q.pick_not_deleted().pick_fastest().get_telemetry(frequency="original")
        except:
            print(f"Couldn't get proper telemetry for {driver}")
            return

        tel = tel[tel["Source"].isin(["pos", "interpolation"])]
        tel.reset_index(drop=True, inplace=True)

        tel["X"] = tel["X"].apply(lambda x: x / 10)
        tel["Y"] = tel["Y"].apply(lambda y: y / 10)
        tel["Z"] = tel["Z"].apply(lambda z: z / 10)

        total_time = str(tel["Time"].iloc[-1])
        # this is a time_delta, we want format: 1:23.342
        # it will be in the format of: 00:01:23.342343
        total_time = total_time.split(" ")[-1][3:12]
        # it looks like if it is exactly 1:12, then there is no decimal
        if len(total_time) == 5:
            total_time += ".000"
        driver_times[driver] = total_time

        driver_tels[driver] = tel

    driver_times: dict[str, str] = {}
    driver_tels: dict[str, Telemetry] = {}
    for driver in driver_abbrevs:
        q1, q2, q3 = laps.pick_driver(driver).split_qualifying_sessions()
        # we want to get the fastest lap for the highest qualifying session which the driver reached

        if q3 is not None:
            process_tel(q3, driver)
        elif q2 is not None:
            process_tel(q2, driver)
        elif q1 is not None:
            process_tel(q1, driver)

    save_driver_times(driver_times, str(year), track)

    return driver_tels


# the data for the start and end of runs from fastf1 is unrelaibale, we can get close to the actual
# start/finish line by getting the average of all the start and end points, it is the same line for
# start and finish. Then, use track data to define a line based on these points, the starting and end
# point of each car will be the part on the line which is closest to the actual data we have for that
# car's start or end point
def process_grouped_driver_tels(driver_tels: dict[str, Telemetry], inner_points, outer_points):
    def get_average_start_end():
        start_points = np.array(
            [[driver_tels[k]["X"].iloc[0], driver_tels[k]["Y"].iloc[0]] for k in driver_tels.keys()]
        )
        end_points = np.array(
            [[driver_tels[k]["X"].iloc[-1], driver_tels[k]["Y"].iloc[-1]] for k in driver_tels.keys()]
        )
        all_points = np.vstack((start_points, end_points))
        return np.mean(all_points, axis=0)

    # using inner_points, outer_points find the idx which is closest to our start/finish line
    # we know that len(inner_points) == len(outer_points)
    def get_line(inner_points, outer_points, start_end_point):
        closest_idx = 0
        closest_dist = float("inf")
        for i, (inner_point, outer_point) in enumerate(zip(inner_points, outer_points)):
            dist_to_inner = (
                (start_end_point[0] - inner_point[0]) ** 2 + (start_end_point[1] - inner_point[1]) ** 2
            ) ** 0.5
            dist_to_outer = (
                (start_end_point[0] - outer_point[0]) ** 2 + (start_end_point[1] - outer_point[1]) ** 2
            ) ** 0.5

            if dist_to_inner + dist_to_outer < closest_dist:
                closest_dist = dist_to_inner + dist_to_outer
                closest_idx = i

        # now, we have two points, the inner and outer points, and we want to represent
        # the line between these two points

        return closest_idx, (inner_points[closest_idx], outer_points[closest_idx])

    # using point_a, point_b, we want to set the start and end points of each driver to be the
    # point on the line between point_a and point_b which is closest to the actual start/end point
    def set_as_closest_to_line(driver_tels, point_a, point_b):
        for _, driver_tel in driver_tels.items():
            original_start = (driver_tel["X"].iloc[0], driver_tel["Y"].iloc[0])
            original_end = (driver_tel["X"].iloc[-1], driver_tel["Y"].iloc[-1])

            def get_closest_point_on_line(point_a, point_b, point):
                # the line is defined by the equation y = mx + b
                m = (point_b[1] - point_a[1]) / (point_b[0] - point_a[0])
                b = point_a[1] - m * point_a[0]

                # the line perpendicular to this line is y = -1/m * x + b2
                m_perp = -1 / m
                b2 = point[1] - m_perp * point[0]

                # now we want to solve for the intersection of these two lines
                x = (b2 - b) / (m - m_perp)
                y = m * x + b

                return (x, y)

            driver_tel["X"].iloc[0], driver_tel["Y"].iloc[0] = get_closest_point_on_line(
                point_a, point_b, original_start
            )
            driver_tel["X"].iloc[-1], driver_tel["Y"].iloc[-1] = get_closest_point_on_line(
                point_a, point_b, original_end
            )

    start_end_point = get_average_start_end()
    line_idx, (point_a, point_b) = get_line(inner_points, outer_points, start_end_point)
    set_as_closest_to_line(driver_tels, point_a, point_b)

    return line_idx


def get_driver_df(tel, s_divisor: int, frames_per_second: int):
    total_distance = 0
    distances = [0.0]
    for i in range(1, len(tel)):
        point_a = (tel["X"][i - 1], tel["Y"][i - 1])
        point_b = (tel["X"][i], tel["Y"][i])

        distance = ((point_a[0] - point_b[0]) ** 2 + (point_a[1] - point_b[1]) ** 2) ** 0.5
        total_distance += distance
        distances.append(total_distance)

    displacements = [a / total_distance for a in distances]

    # we want to set weights such that the spline is forced to go through the start and end points
    weights = np.ones(len(displacements))
    weights[0] = 1000
    weights[-1] = 1000

    spl_x = UnivariateSpline(displacements, tel["X"], w=weights, s=len(displacements) // s_divisor)
    spl_y = UnivariateSpline(displacements, tel["Y"], w=weights, s=len(displacements) // s_divisor)

    # we want to first smooth the speed data using a spline again
    time_floats = tel["Time"].apply(lambda t: t.total_seconds())
    std_time_floats = time_floats / time_floats.max()

    speed_spline = UnivariateSpline(std_time_floats, tel["Speed"], s=len(time_floats))

    frame_count = int(time_floats.max() * frames_per_second)

    # now, we want to sample the spline at 60hz
    sampled_speeds = speed_spline(np.linspace(0, 1, frame_count))

    # now that we have speeds, we can use this to get what % of the track is covered at each frame
    d_covered = [0.0]

    sampled_speeds_m_per_s = np.array(sampled_speeds) / 1000 * frames_per_second

    # first lets find the total d which will be covered based on the speed
    total_d: float = 0.0
    for i in sampled_speeds_m_per_s:
        total_d += i  # because each is over 1/frames_per_second of a second
        d_covered.append(total_d)

    adj_d_covered = [a / total_d for a in d_covered]

    final_x = spl_x(adj_d_covered)
    final_y = spl_y(adj_d_covered)

    # add the first value to the beginning of sampled_speeds_m_per_s so they match length
    sampled_speeds_m_per_s = np.insert(sampled_speeds_m_per_s, 0, sampled_speeds_m_per_s[0])

    return pd.DataFrame(
        {
            "X": final_x,
            "Y": final_y,
            "Z": np.zeros(len(final_x)),
            "Speed": sampled_speeds_m_per_s,
        }
    )


# driver_df has: X, Y, Z, Speed
# get the vector between the first and the second frame, extend that vector infront of the start
def add_start_buffer(driver_df, start_buffer_frames):
    start_x, start_y, start_z = driver_df["X"][0], driver_df["Y"][0], driver_df["Z"][0]
    second_x, second_y, second_z = driver_df["X"][1], driver_df["Y"][1], driver_df["Z"][1]

    x_diff, y_diff, z_diff = second_x - start_x, second_y - start_y, second_z - start_z

    start_speed = driver_df["Speed"][0]
    new_x, new_y, new_z = [], [], []

    prev = (start_x, start_y, start_z)
    for _ in range(start_buffer_frames):
        cur_x, cur_y, cur_z = prev[0] - x_diff, prev[1] - y_diff, prev[2] - z_diff
        new_x.append(cur_x)
        new_y.append(cur_y)
        new_z.append(cur_z)
        prev = (cur_x, cur_y, cur_z)

    # reverse the lists so that the first frame is at the beginning
    new_x = new_x[::-1]
    new_y = new_y[::-1]
    new_z = new_z[::-1]

    new_speeds = [start_speed] * start_buffer_frames
    before_startline_df = pd.DataFrame({"X": new_x, "Y": new_y, "Z": new_z, "Speed": new_speeds})

    driver_df = pd.concat([before_startline_df, driver_df], ignore_index=True)

    driver_df.reset_index(drop=True, inplace=True)
    return driver_df


# driver_df has: X, Y, Z, Speed
# get vector between second to last and last, extend that vector infront of the end
def add_end_buffer(driver_df, end_buffer_frames):
    last_x, last_y, last_z = driver_df["X"].iloc[-1], driver_df["Y"].iloc[-1], driver_df["Z"].iloc[-1]
    second_last_x, second_last_y, second_last_z = (
        driver_df["X"].iloc[-2],
        driver_df["Y"].iloc[-2],
        driver_df["Z"].iloc[-2],
    )

    x_diff, y_diff, z_diff = last_x - second_last_x, last_y - second_last_y, last_z - second_last_z

    start_speed = driver_df["Speed"].iloc[-1]
    new_x, new_y, new_z = [], [], []

    prev = (last_x, last_y, last_z)
    for _ in range(end_buffer_frames):
        cur_x, cur_y, cur_z = prev[0] + x_diff, prev[1] + y_diff, prev[2] + z_diff
        new_x.append(cur_x)
        new_y.append(cur_y)
        new_z.append(cur_z)
        prev = (cur_x, cur_y, cur_z)

    new_speeds = [start_speed] * end_buffer_frames
    after_endline_df = pd.DataFrame({"X": new_x, "Y": new_y, "Z": new_z, "Speed": new_speeds})

    driver_df = pd.concat([driver_df, after_endline_df], ignore_index=True)

    driver_df.reset_index(drop=True, inplace=True)
    return driver_df


def add_car_rots(df):
    points = [(df["X"][i], df["Y"][i], df["Z"][i]) for i in range(len(df))]

    def get_rots(points, lookahead_points=20, slerp_val=0.1):
        # Previous rotation quaternion for SLERP
        prev_rot = None
        rot_w = []
        rot_x = []
        rot_y = []
        rot_z = []

        for i, point in enumerate(points):
            # Define how far ahead we look based on available points
            lookahead = min(lookahead_points, len(points) - i - 1)

            combined_pos = mathutils.Vector(point)
            for j in range(1, lookahead + 1):
                combined_pos += mathutils.Vector(points[i + j])

            combined_pos /= lookahead + 1
            direction = combined_pos - mathutils.Vector(point)

            # Calculate rotation to track direction
            rot_quat = direction.to_track_quat("-Y", "Z")

            if prev_rot and rot_quat:
                # Interpolate between previous and current quaternion
                rot_quat = prev_rot.slerp(rot_quat, slerp_val)

            rot_w.append(rot_quat.w)
            rot_x.append(rot_quat.x)
            rot_y.append(rot_quat.y)
            rot_z.append(rot_quat.z)

            # Update previous rotation
            prev_rot = rot_quat

        return rot_w, rot_x, rot_y, rot_z

    rot_w, rot_x, rot_y, rot_z = get_rots(points)
    df["RotW"] = rot_w
    df["RotX"] = rot_x
    df["RotY"] = rot_y
    df["RotZ"] = rot_z

    harsher_rot_w, harsher_rot_x, harsher_rot_y, harsher_rot_z = get_rots(points, lookahead_points=2, slerp_val=0.05)
    df["HarsherRotW"] = harsher_rot_w
    df["HarsherRotX"] = harsher_rot_x
    df["HarsherRotY"] = harsher_rot_y
    df["HarsherRotZ"] = harsher_rot_z

    return df


# angular velocity is calculated as v/r where v is linear velocity or 10 m/s for example and r is 0.33 meters
def add_wheel_rots(df):
    prev_rot = 0  # this is arbitrary but shouldnt matter because it is a wheel
    tire_rots = []
    for i in range(len(df)):
        rad_per_s = df["Speed"][i] / 0.33
        new_rot = -(prev_rot + rad_per_s / 60)  # should rotate in negative x, this is arbitrary, relative to the model
        tire_rots.append(new_rot)
        prev_rot = new_rot

    df["TireRot"] = tire_rots
    return df


def save(year: str, track: str, fps: str, dfs: dict[str, pd.DataFrame], start_finish_line_idx: int):
    cur_dir = DriverDataPS.get_car_data_dir(year, track, fps)
    os.makedirs(cur_dir, exist_ok=True)

    for driver, df in dfs.items():
        driver_path = DriverDataPS.get_car_data_path(year, track, fps, driver)
        df.to_csv(driver_path, index=False)

    with open(os.path.join(cur_dir, "start_finish_line_idx.txt"), "w") as file:
        file.write(str(start_finish_line_idx))


def already_done(year: str, track: str, fps: str):
    cur_dir = DriverDataPS.get_car_data_dir(year, track, fps)
    start_finish_line_idx = 0

    if os.path.exists(cur_dir):
        driver_dfs = {}
        for driver in os.listdir(cur_dir):
            if driver == "start_finish_line_idx.txt":
                with open(os.path.join(cur_dir, driver), "r") as file:
                    start_finish_line_idx = int(file.read())
                continue
            driver_path = os.path.join(cur_dir, driver)
            driver_dfs[driver.split(".")[0]] = pd.read_csv(driver_path)

        return True, driver_dfs, start_finish_line_idx

    return False, {}, start_finish_line_idx


# if all 4 wheels go off the track, then they are out of track limits
# we already checked that none of these runs were disqualified so we can assume
# that in real life non went off limits, therefore the smoothing shouldnt cause them to here
def in_track_limits(driver_df: pd.DataFrame, track_edges: pd.DataFrame):
    # find the closest point on the track to the driver's position, it must be within 1 meter
    for i in range(len(driver_df)):
        cur_point = (driver_df["X"][i], driver_df["Y"][i])
        for j in range(len(track_edges)):
            track_point_inner = (track_edges["inner_X"][j], track_edges["inner_Y"][j])
            track_point_outer = (track_edges["outer_X"][j], track_edges["outer_Y"][j])

            dist_inner = (
                (cur_point[0] - track_point_inner[0]) ** 2 + (cur_point[1] - track_point_inner[1]) ** 2
            ) ** 0.5
            dist_outer = (
                (cur_point[0] - track_point_outer[0]) ** 2 + (cur_point[1] - track_point_outer[1]) ** 2
            ) ** 0.5

            if dist_inner > 1 or dist_outer > 1:
                return False

    return True


def optimize_smoothness(track_edges: pd.DataFrame, fps: int, driver_tels: dict[str, Telemetry]):
    dfs: dict[str, pd.DataFrame] = {}

    s_divisor = 3  # increasing this s_divisor will make the spline more rigid
    max_s_divisor = 10

    found_max_smoothness = False
    while not found_max_smoothness:
        if s_divisor > max_s_divisor:
            print("Using max smoothness, this means something is probably wrong...")
            for driver, tel in driver_tels.items():
                dfs[driver] = get_driver_df(tel, s_divisor, fps)

        for driver, tel in driver_tels.items():
            dfs[driver] = get_driver_df(tel, s_divisor, fps)

            if not in_track_limits(dfs[driver], track_edges):
                s_divisor += 1
                break

        found_max_smoothness = True

    return dfs


def generate_df_and_eval_track_limit(tel, s_divisor, fps, track_edges):
    df = get_driver_df(tel, s_divisor, fps)
    in_limits = in_track_limits(df, track_edges)

    return df, in_limits


def optimize_smoothness_concurrent(track_edges: pd.DataFrame, fps: int, driver_tels: dict[str, Telemetry]):
    driver_dfs = {}

    s_divisor = 3
    max_s_divisor = 10
    found_optimal = False

    while not found_optimal:
        print("Checking s_divisor: ", s_divisor)
        found_optimal = True

        with ThreadPoolExecutor() as executor:
            futures = {
                executor.submit(generate_df_and_eval_track_limit, tel, s_divisor, fps, track_edges): driver
                for driver, tel in driver_tels.items()
            }

            for future in concurrent.futures.as_completed(futures):
                df, in_limits = future.result()
                if not in_limits:
                    found_optimal = False

                driver_dfs[futures[future]] = df

        if not found_optimal:
            s_divisor += 1

        if s_divisor > max_s_divisor:
            print("Using max smoothness, this means something is probably wrong...")
            break

    return driver_dfs


# in order to run this function, we need to already have the track data for this track and year
# because this will be necessary to ensure that we have the correct smoothness so the movement
# looks natural but also so that we are within track limits
def main(config, track_data):
    is_done, driver_dfs, start_finish_line_idx = already_done(
        str(config["year"]), config["track"], str(config["render"]["fps"])
    )
    if is_done:
        print("Already fetched this car data, don't need to load...")
        return driver_dfs, start_finish_line_idx
    print("Fetching and processing car data")

    driver_tels = load_from_fastf1(config["year"], config["track"])
    start_finish_line_idx = process_grouped_driver_tels(driver_tels, track_data.inner_points, track_data.outer_points)

    driver_dfs = {}
    for driver, tel in driver_tels.items():
        df = get_driver_df(tel, 3, track_data["fps"])
        df = add_start_buffer(df, config["render"]["start_buffer_frames"])
        df = add_end_buffer(df, config["render"]["end_buffer_frames"])
        driver_dfs[driver] = df

    for driver, df in driver_dfs.items():
        df = add_car_rots(df)
        df = add_wheel_rots(df)
        driver_dfs[driver] = df

    save(str(config["year"]), config["track"], str(config["fps"]), driver_dfs, start_finish_line_idx)

    print(f"Done processing car data")
    return driver_dfs, start_finish_line_idx
