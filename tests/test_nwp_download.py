"""
This script tests the successful donwloading of ICON-D2 data

Functions:
- test_icon_download: Tests that the downloaded creates the expected files at the expected location
  and the derived city aggregtes cover the expected parameters.
"""

import datetime
import os

import pandas as pd

from src.icon_d2.src import main as icon_download_main

from .test_utils import clear_tmp_dir

# This should include the same variables as the ones downloaded by the icon_d2 module.
REQUESTED_VARS = [
    "t_2m",
    "relhum_2m",
    "u_10m",
    "v_10m",
    "asob_s",
    "tot_prec",
    "ASWDIR_S",
    "ASWDIFD_S",
]


def test_icon_download():
    """
    Tests the output of d2r_icon2d Downloading tool to be
    at the expected location and for the requested hours
    """
    # create parameters
    request_date = datetime.datetime.now().isoformat()
    save_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "tmp", "icon-download"
    )
    clear_tmp_dir(save_dir)

    # run function
    icon_download_main.get_icon2d_nwp(
        date=request_date, hours_to_nwp_run=4, start=0, step=1, end=4, save_dir=save_dir
    )

    # check output file
    subdirs = os.listdir(save_dir)
    assert len(subdirs) == 1, "save_dir should contain exactly one subfolder"

    # check output variables
    calculated_vars = ["wind_dir", "wind_speed", "thermalcomfort"]
    expected_vars = [*REQUESTED_VARS, *calculated_vars]
    var_counter = 0
    unwanted_vars = 0
    other_files = []
    for entry in os.listdir(os.path.join(save_dir, subdirs[0])):
        # check if expected vars are in nwp folder
        if ".nc" in entry:
            if any(x in entry for x in expected_vars):
                var_counter += 1
            else:
                unwanted_vars += 1
        else:
            # other files are irrelevant
            other_files.append(entry)

    assert var_counter == len(
        expected_vars
    ), f"Download should create one netCDF file for each of the {len(expected_vars)} expected variables, but found {var_counter}"
    assert (
        unwanted_vars == 0
    ), f"Unknown netCDF files ({len(expected_vars)} in total) found in the savedir used by the NWP download script."
    assert (
        len(other_files) == 1
    ), "Only one non-nc-file should be created during this process."
    assert (
        other_files[0] == "city_means.csv"
    ), "The one non-nc-file should be called 'city_means.csv'."

    df = pd.read_csv((os.path.join(save_dir, subdirs[0], other_files[0])))
    assert len(list(df.columns)) == len(
        expected_vars
    ), "Derived city means should only refer to expected variables."
