import subprocess
import sys

import load_ff1
import load_track_data
import yaml


def read_from_yaml():
    with open("conf.yaml", "r") as file:
        config = yaml.safe_load(file)

    year = config["year"]
    track = config["track"]
    fps = config["render"]["fps"]

    assert isinstance(year, int)
    assert isinstance(track, str)
    assert isinstance(fps, int)

    drivers = []
    for driver in config["drivers"]:
        name = driver["name"]
        color = driver["color"]

        assert isinstance(name, str)
        assert isinstance(color, str)

        drivers.append((name, color))

    print("Received Config:")
    print(f"    Year: {year}")
    print(f"    Track: {track}")
    print(f"    FPS: {fps}")
    print("Drivers:")
    for driver in drivers:
        print("    " + str(driver))

    return year, track, fps, drivers


if __name__ == "__main__":
    read_args_from_yaml = sys.argv[1] == "yaml"

    if read_args_from_yaml:
        year, track, fps, _ = read_from_yaml()

        track_df = load_track_data.main(year, track)
        load_ff1.main(year, track, fps)
    # there will be 2 options here because this file may either be run from the main
    # render script, or from the tdc_gui script in order to generate the car data for
    # the track edges. If this is within render, then it uses the yaml as standard
    # however, if there are more arguments, then we default to reading year, track, fps
    # from args instead of from yaml because the yaml will not be present/correct in that case
    else:
        year = int(sys.argv[2])
        track = sys.argv[3]
        fps = int(sys.argv[4])

        # if calling from script, naturally we just don't call the load_track_data because
        # it has not been generated yet at this point and we aren't using this for the actual render
        load_ff1.main(year, track, fps)
