"""
Script to replace ta and rh entries in a given city_means.csv

This is used to merge the meteorological information from the different
workflows (interpolation & ICON) into a single forcing file for SOLWEIG.

"""

import argparse
import datetime
import logging
import os

import pandas as pd


def replace_ta_rh(ta_means: str, rh_means: str, city_means: str, output_path: str):
    """
    Replace air temperature and relative humidity values in given city means file
    with those given in the respective files. Save the result at the given path.

    Args:
        ta_means(str): path to air temperature means file in csv format
        rh_means(str): path to relative humidity means file in csv format
        city_means(str): path to city means file generated from ICON-D2 nwp
        output_path(str): path to save the results
    """

    # read inteprolation data for two hours
    ta_df = pd.read_csv(ta_means)
    ta_df = ta_df.rename(
        columns={"year": "iy", "doy": "id", "hour": "it", "value": "Tair"}
    )
    rh_df = pd.read_csv(rh_means)
    rh_df = rh_df.rename(
        columns={"year": "iy", "doy": "id", "hour": "it", "value": "RH"}
    )
    # read ICON-D2 NWP data for 48 hours
    df = pd.read_csv(city_means, sep=" ")

    # remove existing Tair and RH entries retrieved from ICON-D2
    df = df.drop(["RH", "Tair"], axis=1)

    # add available data for Tair and RH from interpolation data to the end of the df
    df = df.join(ta_df.set_index(["iy", "id", "it"]), on=["iy", "id", "it"])
    df = df.join(rh_df.set_index(["iy", "id", "it"]), on=["iy", "id", "it"])
    # for completeness: fill remaining fields with -999 = UMEP's No Data Value
    df = df.fillna(-999)
    # Note: the following steps of the pipeline are designed to only consider
    #  the two filled hours and crop all the others.

    # reorder columns as expected by UMEP
    column_order = [
        "iy",
        "id",
        "it",
        "imin",
        "qn",
        "qh",
        "qe",
        "qs",
        "qf",
        "U",
        "RH",
        "Tair",
        "pres",
        "rain",
        "kdown",
        "snow",
        "ldown",
        "fcld",
        "Wuh",
        "xsmd",
        "lai",
        "kdiff",
        "kdir",
        "wdir",
    ]

    entry = df.iloc[-1]  # last entry = the hour to be modelled
    year = entry["iy"]
    date = datetime.datetime(int(year), 1, 1) + datetime.timedelta(int(entry["id"]) - 1)
    month = date.month
    day = date.day
    hour = int(entry["it"])

    if not os.path.exists(os.path.dirname(output_path)):
        logging.error(f"Output path {output_path} does not exist. Exiting..")
        exit(1)
    logging.info(f"Writing metfile to {output_path}")
    df.to_csv(output_path, columns=column_order, sep=" ", index=False)

    return output_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--tair", help="Path to air temperature file.")
    parser.add_argument("-r", "--relhum", help="Path to relative humidity file.")
    parser.add_argument("-m", "--city_means", help="Path to icon-d2 means file.")
    parser.add_argument("-o", "--output_path", help="Path to output dir.")

    args = parser.parse_args()

    replace_ta_rh(
        ta_means=args.tair,
        rh_means=args.relhum,
        city_means=args.city_means,
        output_path=args.output_path,
    )
