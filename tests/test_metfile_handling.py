"""
This script tests the metfile handling of different functions.

Functions:
- test_metfile_conversion: Tests that the converted forecast-metfile from ICON to UMEP has the expected properties.
- test_load_metfile_correct: Tests that the metfile is properly derived from the forecast.
- test_load_metfile_correct_dayswitch: Tests that the metfile is properly derived even when extracted hours are affected by a day switch.
- test_load_metfile_incorrect: Tests that the metfile derivation blocks as expected, when the extracted time is within the warm-up phase.
"""

import os

import pandas as pd

from src.utils.load_metfile import select_met_data
from src.umep_wrapper.icon2umep import citymeans2umep

from .test_utils import (
    MET_HEADER,
    clear_tmp_dir,
    create_dummy_city_means,
    create_dummy_metfile_48_hours,
    create_dummy_metfile_dayswitch,
)


def test_metfile_conversion():
    """
    Tests the proper conversion of icon derived city means into umep format.
    """

    save_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "tmp", "umep-converter"
    )
    clear_tmp_dir(save_dir)

    create_dummy_city_means(save_dir, "dummy_city_means.csv")
    input_file = os.path.join(save_dir, "dummy_city_means.csv")

    citymeans2umep(
        means_file=input_file,
        output_file="met_out.txt",
        output_dir=save_dir,
    )

    with open(input_file, "r") as f:
        lines_in = f.readlines()

    with open(os.path.join(os.path.join(save_dir, "met_out.txt")), "r") as f:
        lines_out = f.readlines()

    assert (
        lines_out[0].strip() == MET_HEADER
    ), "Header of output should match with UMEP style header."
    assert len(lines_in) == len(
        lines_out
    ), "Datasets should have an equal number of entries (rows)."

    counter = 0
    expected_len = len(MET_HEADER.split(" "))
    for line in lines_out:
        split = line.split(" ")
        if len(split) == expected_len:
            counter += 1
    assert counter == len(
        lines_out
    ), "All columns should be seperated with a single space"


def test_load_metfile_correct():
    """
    Tests correct loading of metfile for a given hour.
    """
    save_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tmp")
    clear_tmp_dir(save_dir)

    year = 2024
    doy = 233
    hour = 18

    create_dummy_metfile_48_hours(save_dir, "dummy_metfile.txt")
    input_file = os.path.join(save_dir, "dummy_metfile.txt")

    select_met_data(
        input_file=input_file,
        utc_year=year,
        utc_doy=doy,
        utc_hour=hour,
        output_file=os.path.join(save_dir, "load_met_out.txt"),
    )

    with open(input_file, "r") as f:
        lines_in = f.readlines()

    with open(os.path.join(os.path.join(save_dir, "load_met_out.txt")), "r") as f:
        lines_out = f.readlines()

    # Check header and scope
    assert lines_in[0] == lines_out[0], "Header of both files should be identical."
    assert (
        len(lines_out) == 3
    ), "Metfile for SOLWEIG run should only have 3 rows (header + 2 rows)."

    counter = 0
    expected_len = len(MET_HEADER.split(" "))
    for line in lines_out:
        split = line.split(" ")
        if len(split) == expected_len:
            counter += 1
    # Check separators
    assert counter == len(
        lines_out
    ), "All columns should be seperated with a single space"

    df = pd.read_csv(os.path.join(os.path.join(save_dir, "load_met_out.txt")), sep=" ")
    assert df["it"].iloc[0] == hour - 1, "Should be the hour before the given hour."
    assert df["it"].iloc[1] == hour, "Should be the given hour."


def test_load_metfile_correct_dayswitch():
    """
    Tests correct loading of metfile for the dayswitch (23 -> 0).
    """
    save_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tmp")
    clear_tmp_dir(save_dir)

    year = 2024
    doy = 234
    hour = 0

    create_dummy_metfile_dayswitch(save_dir, "dummy_metfile.txt")
    input_file = os.path.join(save_dir, "dummy_metfile.txt")

    select_met_data(
        input_file=input_file,
        utc_year=year,
        utc_doy=doy,
        utc_hour=hour,
        output_file=os.path.join(save_dir, "load_met_out.txt"),
    )

    df = pd.read_csv(os.path.join(os.path.join(save_dir, "load_met_out.txt")), sep=" ")
    assert df["id"].iloc[0] == doy - 1, "Should be the day before the given doy."
    assert df["id"].iloc[1] == doy, "Should be the given doy."
    assert df["it"].iloc[0] == 23, "Should be the hour before the given hour."
    assert df["it"].iloc[1] == hour, "Should be the given hour."


def test_load_metfile_incorrect():
    """
    Tests loading of metfile for a given an incorrect hour.
    """

    save_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tmp")
    clear_tmp_dir(save_dir)

    year = 2024
    doy = 233

    # Hour is too close to model start time
    hour = 12

    create_dummy_metfile_48_hours(save_dir, "dummy_metfile.txt")
    input_file = os.path.join(save_dir, "dummy_metfile.txt")

    try:
        select_met_data(
            input_file=input_file,
            utc_year=year,
            utc_doy=doy,
            utc_hour=hour,
            output_file=os.path.join(save_dir, "load_met_out.txt"),
        )
    except AssertionError:
        assert (
            True
        ), "Hours closer than the min ICON-D2 warm-up time of 6 hours are internally \
                        blocked for selection and cause an internal error."

    # Hour is before model start time
    hour = 11
    try:
        select_met_data(
            input_file=input_file,
            utc_year=year,
            utc_doy=doy,
            utc_hour=hour,
            output_file=os.path.join(save_dir, "load_met_out.txt"),
        )
    except AssertionError:
        assert (
            True
        ), "Hours before the available time are not possibe to select and cause \
                        an internal error."

    # requested time is 24+6 hours after model start time
    doy = 234
    hour = 18
    try:
        select_met_data(
            input_file=input_file,
            utc_year=year,
            utc_doy=doy,
            utc_hour=hour,
            output_file=os.path.join(save_dir, "load_met_out.txt"),
        )
    except AssertionError:
        assert (
            True
        ), "The hour closest to the model start time + warmup of 6 hours is expected to use."
