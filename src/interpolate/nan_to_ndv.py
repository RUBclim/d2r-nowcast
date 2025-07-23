"""
Script to transform np.nan values from a raster to a
given NoDataValue (ndv) with the default being -32768.

This is used to unify the interpolation results from np.nan to
the commonly used ndv in the pipeline.
"""

import argparse
import sys

import numpy as np
from osgeo import gdal

# import utility script from relativ path for script execution
libPath = "../../utils"
if not libPath in sys.path:
    sys.path.append(libPath)
from utils.save_raster import saveraster

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("file", help="GeoTiff with nan values.")
    parser.add_argument("--ndv", help="The no data value to be used", default=-32768)

    args = parser.parse_args()

    src = gdal.Open(args.file, gdal.GA_ReadOnly)
    dst = np.nan_to_num(src.ReadAsArray(), nan=args.ndv)

    output_location = args.file.split(".")[0] + "_ndv.tif"

    saveraster(src, output_location, dst)
