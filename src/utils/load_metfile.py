"""
This script is used to select relevant hours from meteorological data for SOLWEIG run.
It also holds a writing and cli functionality.
"""

import argparse
import datetime

import pandas as pd

HEADER = "iy id it imin qn qh qe qs qf U RH Tair pres rain kdown snow ldown fcld Wuh xsmd lai kdiff kdir wdir"


def select_met_data(
    input_file: str, utc_year: int, utc_doy: int, utc_hour: int, output_file: str
):
    """
    Selects data from an input meteorological data file that holds hourly
    averaged values over the area of interest derived from ICON-D2 NWP for
    the given timestamp and the previous hour in UMEP-accepted format and
    writes it to a separate output file.
    Note that the input file is given in UTC! The timestamp therefore also has
    to be in UTC, to get the correct meteo data.
    Note: If the given timestamp is not in the input_file or lays within the
    warm-up phase of the model (6 hours) an assertion error will be shown.

    Args:
        input_file (str): Input meteo data file with hourly entries
        utc_year (int): The year (in UTC)
        utc_doy (int): The day of the year (in UTC)
        utc_hour (int): The hour (in UTC)
        output_file (str): Output file name
    """

    df = pd.read_csv(input_file, sep=" ")

    # assert that request year is in dataframe
    # NOTE: we use the most recent ICON forecast that ran at least 6 hours
    # so the index in the dataframe that matches the request is
    # 6-1 (0-based data structure) + (hour-1) modulo modelIntervalHours
    minimum_model_runtime = 6  # model ran at least 6 hours
    model_interval_hours = 3  # icon2d updates every 3 hours
    entry = minimum_model_runtime + utc_hour % model_interval_hours
    assert (
        df["iy"].values[entry] == utc_year
    ), f'Year of entry should be {utc_year} and not {df["iy"].values[entry]}'
    assert (
        df["id"].values[entry] == utc_doy
    ), f'Doy of entry should be {utc_doy} and not {df["id"].values[entry]}.'
    assert (
        df["it"].values[entry] == utc_hour
    ), f'Hour of entry should be {utc_hour} and not {df["it"].values[entry]}.'
    # select two hours, the requested and the one before it
    new_df = df.iloc[[entry - 1, entry]]

    # set timestamp as index:
    new_df = new_df.astype(
        {"iy": "int32", "id": "int32", "it": "int32", "imin": "int32"}
    )

    new_df.to_csv(output_file, sep=" ", index=False)


def write_metfile(file_name: str, save_dir: str, content: str):
    """Writes metfile data to files"""

    with open(file_name, "w") as file:
        print(f"Saving metfile at {file_name}")
        file.write(HEADER + "\n")
        file.write(content + "\n")

    with open(f"{save_dir}/metfile_latest.txt", "w") as file:
        file.write(HEADER + "\n")
        file.write(content + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--savedir", help="The savedir of the output file, e.g. ~/data/metfiles"
    )
    parser.add_argument(
        "--input",
        help="Path to an existing met csv file that contains more hours than required.",
    )
    parser.add_argument("--year", help="selected year")
    parser.add_argument("--month", help="selected month")
    parser.add_argument("--day", help="selected day")
    parser.add_argument("--hour", help="selected hour")
    parser.add_argument(
        "--proc", help="Processing path that was used to create the met data"
    )

    args = vars(parser.parse_args())
    year = int(args["year"])
    month = int(args["month"])
    day = int(args["day"])
    hour = int(args["hour"])
    doy = datetime.datetime(year, month, day, hour, 00, 00).timetuple().tm_yday

    # TODO: maybe add validation of parameters

    filename = f"{args['savedir']}/metfile_{args['proc']}_{year}-{month:02d}-{day:02d}_{hour:02d}00.txt"
    select_met_data(
        input_file=args["input"],
        utc_year=year,
        utc_doy=doy,
        utc_hour=hour,
        output_file=filename,
    )
