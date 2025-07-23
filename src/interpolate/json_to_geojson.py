"""
A script to transform station data json file downloaded
dynamically from https://api.data2resilience.de/ into geojson
with fields expected from the interpolation module.
The CRS used for the transformation is hard coded (from EPSG:4326 to EPSG:25832)
and has to be adjusted manually, if input differs from it.
"""

import argparse
import datetime
import json
import os

import requests
from pyproj import Transformer


def transform(data: dict, output_dir: str = ""):
    """
    Transform station data in json format into geojson format with expected
    fields for the interpolation module.
    Note, the CRS used is hard coded (transform from EPSG:4326 to EPSG:25832)
    and has to be adjusted manually, if input differs from it.

    Args:
        data_json_str (str): station data as json str given in EPSG:4326
    Returns:
        output filename (str)

    """
    # target format GeoJSON
    geojson = {
        "type": "FeatureCollection",
        "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:EPSG::25832"}},
        "features": [],
    }

    # define the crs transformer
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:25832")

    # transform
    for entry in data["data"]:
        x, y = transformer.transform(entry["latitude"], entry["longitude"])

        feature = {
            "type": "Feature",
            "properties": {
                "name": entry["station_id"],
                "long_name": entry["long_name"],
                "station_type": entry["station_type"],
                "measured_at": entry["measured_at"],
                "air_temperature": entry["air_temperature"],
                "relative_humidity": entry["relative_humidity"],
            },
            "geometry": {"type": "Point", "coordinates": [x, y]},
        }
        geojson["features"].append(feature)

    # save into file
    if (output_dir != "") and (not os.path.exists(output_dir)):
        os.makedirs(output_dir)
        print(f"Created output_dir {output_dir}")

    output_path = os.path.join(output_dir, f'station_data_{data["timestamp"]}.geojson')
    with open(output_path, "w") as f:
        json.dump(geojson, f, ensure_ascii=False, indent=4)
    return output_path, len(data["data"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-o",
        "--output_dir",
        help="Path to output dir, default is current dir.",
        default="",
    )
    parser.add_argument(
        "-s",
        "--step",
        help="Whether data for the current or a previous hour should be loaded, one of 'now', 'prev'.",
        default="now",
    )
    parser.add_argument(
        "-m",
        "--max_age",
        help="Considered time window in minutes, for 'prev' setting.",
        default=15,
    )
    parser.add_argument("-d", "--date", help="ISO timestamp UTC, for 'prev' setting.")

    args = parser.parse_args()

    # get data
    if args.step == "now":
        # download latest data per station not older than 15 minutes
        url = "https://api.data2resilience.de/v1/stations/latest_data?param=air_temperature&param=relative_humidity&max_age=PT15M"
        response_API = requests.get(url, headers={"content-type": "application/json"})
        # read data
        data = json.loads(response_API.text)
    else:
        assert (
            args.step == "prev"
        ), f"Argument 'step' was neither 'now' nor 'prev', got {args.step}."

        # download data for all station in the given time window
        end_date = datetime.datetime.fromisoformat(args.date)
        start_date = end_date - datetime.timedelta(minutes=int(args.max_age))

        url = "https://api.data2resilience.de/v1/stations/metadata?param=long_name&param=station_type&param=latitude&param=longitude&include_inactive=false"
        response_API = requests.get(url, headers={"content-type": "application/json"})
        meta_data = json.loads(response_API.text)

        stations = [entry["station_id"] for entry in meta_data["data"]]

        # simulate 'latest data' for previous hour
        station_data = []
        for station_id in stations:
            url = f"https://api.data2resilience.de/v1/data/{station_id}?start_date={start_date.strftime('%Y-%m-%dT%H:%M:%SZ')}&end_date={end_date.strftime('%Y-%m-%dT%H:%M:%SZ')}&param=air_temperature&param=relative_humidity&scale=max"
            response_API = requests.get(
                url, headers={"content-type": "application/json"}
            )
            measurement_data = json.loads(response_API.text)

            station_meta_data = [
                e for e in meta_data["data"] if e["station_id"] == station_id
            ][0]
            if len(measurement_data["data"]) != 0:
                entry = measurement_data["data"][
                    -1
                ]  # air_temperature, relative_humidity, measured_at
                entry["station_id"] = station_id
                entry["long_name"] = station_meta_data["long_name"]
                entry["station_type"] = station_meta_data["station_type"]
                entry["latitude"] = station_meta_data["latitude"]
                entry["longitude"] = station_meta_data["longitude"]

                station_data.append(entry)

        data = {"data": station_data, "timestamp": meta_data["timestamp"]}

    # transform data to correct epsg and write into a geojson file
    filename, n_points = transform(data, output_dir=args.output_dir)

    # make filename accessible from outside the scripts
    print(filename, n_points)
