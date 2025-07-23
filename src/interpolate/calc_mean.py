"""
Script to calculate the hourly mean of two rasters corresponding to two consecutive hours
and create a dataframe with one row per timestep.
This is used as one component to generate the meteorological forcing file for SOLWEIG.
"""

import argparse
import json
import logging
import os
import re
from datetime import datetime, timedelta

import numpy as np

# import rasterio as rio
import pandas as pd
from osgeo import gdal

gdal.UseExceptions()


def calc_mean(prev: str, now: str, output_path: str):
    """
    Calculates the hourly mean of given rasters in the limited area and saves it.

    Note that the rasters are assumed to be already masked to the relevant area
    (with -32768 as NAN value) and for which the mean is calculated.

    Args:
        prev (str): path to previous hour raster geotiff
        now (str): path to current hour raster geotiff
        output_path (str): path to save results
    """

    # Create the initial datetime object

    pattern = r"^DO_(TA|RH)_(?P<YEAR>\d{4})_interpolate-(?P<FLOAT>\d\.\d)_(?P<DOY>\d{3})_(?P<HOUR>\d{2})_(prev_align|align).tif$"
    if not re.match(pattern, prev) and re.match(pattern, now):
        logging.warn(
            f"filenames of prev or now are not matching the expected pattern. prev: {prev}, now: {now}, expected {pattern} \n Exiting .."
        )
        exit(1)

    # derive current date of 'now'
    segments = os.path.basename(now).split("_")
    year = int(segments[3])
    doy = int(segments[4])
    hours = int(segments[5])

    now_date = datetime(year, 1, 1) + timedelta(days=doy - 1, hours=hours)
    # Subtract 1 hour for 'prev'
    prev_date = now_date - timedelta(hours=1)

    # collect data for means file
    years = []
    doys = []
    hours = []
    means = []

    # start loop with previous hour
    date = prev_date
    for raster in [prev, now]:
        # read raster
        arr = gdal.Open(raster, gdal.GA_ReadOnly).ReadAsArray()
        # collect data for means file
        years.append(date.year)
        doys.append(date.timetuple().tm_yday)
        hours.append(date.hour)
        # calc mean
        arr[arr == -32768] = np.nan
        means.append(np.round(np.nanmean(arr), 2))

        # set date to date of next step = date of 'now'
        date = now_date

    df = pd.DataFrame({"year": years, "doy": doys, "hour": hours, "value": means})
    df.to_csv(output_path, index=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--prev", help="File path to data of previous hour.")
    parser.add_argument("-n", "--now", help="File path to data of current hour.")
    parser.add_argument("-o", "--output", help="Output file path.")

    args = parser.parse_args()

    calc_mean(prev=args.prev, now=args.now, output_path=args.output)
