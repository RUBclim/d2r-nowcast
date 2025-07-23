"""
Get the latest NWP for Dortmund.
"""

import math
from argparse import ArgumentParser
from datetime import datetime, timedelta

from icon_d2.src.comfort import calc_indices
from icon_d2.src.download import download_nwp
from icon_d2.src.process import calc_city_means, combine_wind_components


def get_icon2d_nwp(
    date: str,
    hours_to_nwp_run: int,
    start: int,
    step: int,
    end: int,
    save_dir: str = "./data",
) -> dict:
    """Get the specified NWP for Dortmund and calculate thermal comfort
    indices from NWP data.

    Args:
       date (str): specific timestamp in isoformat YYYY-MM-DDTHH:MM:SS
       hours_to_nwp_run (int): time difference to an NWP (0 = latest)
       start (int): Forecast start time
       step (int): Forecast timestep
       end (int): Forecast end time
       save_dir (str, optional): Path to download location. Defaults to "./data".

    """
    assert hours_to_nwp_run >= 0, "Difference to run has to be in [0,23]"
    assert hours_to_nwp_run <= 23, "Difference to run has to be in [0,23]"
    assert start < end, "Forecast start time has to be smaller than end time"
    assert step < end, "Forecast timestep has to be smaller than end time"

    # derive timestamp from given date or current time
    if date is not None:
        timestamp = datetime.fromisoformat(date)
        if hours_to_nwp_run is not None:
            timestamp = timestamp - timedelta(hours=hours_to_nwp_run)
    else:
        timestamp = datetime.utcnow() - timedelta(hours=hours_to_nwp_run)

    model_interval_hours = 3  # 3 hours for icon2d
    latest_available_utc_run = int(
        math.floor(timestamp.hour / model_interval_hours) * model_interval_hours
    )
    model_timestamp = datetime(
        timestamp.year, timestamp.month, timestamp.day, latest_available_utc_run
    )

    settings = {
        "model": "icon-d2",
        "grid": "regular-lat-lon",
        "fields": (
            "t_2m",
            "relhum_2m",
            "u_10m",
            "v_10m",
            "asob_s",
            "tot_prec",
            "ASWDIR_S",
            "ASWDIFD_S",
        ),
        "start": start,  # forecast start time
        "end": end,  # forecast end time
        "step": step,  # forecast timestep
        "timestamp": str(model_timestamp),  # request the latest available data
        "roi": ("6.2", "7.8", "50.7", "51.7"),  # (W, E, S, N) coords in degrees.
        "savedir": save_dir,  # NWP savedir
    }

    print(f"Requesting DWD data with the following settings\n{settings}")
    nwp = download_nwp(settings)

    print("Calculating wind speed and direction\n")
    nwp = combine_wind_components(nwp)

    print("Aggregating data to city level\n")
    nwp["city_means"] = calc_city_means(nwp)

    print("Calculating thermal comfort indices\n")
    nwp["indices"] = calc_indices(nwp)

    return nwp


if __name__ == "__main__":

    parser = ArgumentParser(description="A tool to download DWD's ICON-D2 NWP.")

    parser.add_argument(
        "-d",
        "--date",
        type=str,
        help="Specific timestamp in isoformat YYYY-MM-DDTHH:MM:SS",
    )
    parser.add_argument(
        "-t",
        "--time_to_nwp",
        type=int,
        help="Time difference to an NWP (0 = latest)",
        default=0,
    )
    parser.add_argument(
        "-a",
        "--start",
        type=int,
        help="Forecast start time [0, 48]",
        default=0,
    )
    parser.add_argument(
        "-s",
        "--step",
        type=int,
        help="Forecast timestep (e.g. 2 = every second prediction) [1, --end]",
        default=4,
    )
    parser.add_argument(
        "-e",
        "--end",
        type=int,
        help="Forecast end time [--start, 48]",
        default=8,
    )
    parser.add_argument(
        "-o",
        "--save_dir",
        type=str,
        help="Path to download location",
        default="./data",
    )

    # arguments to dictionary
    args = vars(parser.parse_args())
    print(f"Input Parameters for ICON-D2 downloading script are\n{args}")

    get_icon2d_nwp(
        date=args["date"],
        hours_to_nwp_run=args["time_to_nwp"],
        start=args["start"],
        step=args["step"],
        end=args["end"],
        save_dir=args["save_dir"],
    )
