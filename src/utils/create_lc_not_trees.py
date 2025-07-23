"""
This scripts changes land cover of trees to land cover underneath trees.
It only creates valid SOLWEIG input land cover files, if the input lc files
consist of classes between 1 and 7.
"""

import argparse
import glob
import os

import numpy as np
from osgeo import gdal

# import from umep_processing_fork packages
from util.misc import saveraster

gdal.UseExceptions()


def main(lc_path: str, out_path: str):
    """
    Generates a UMEP compatible land cover(lc) raster from an existing lc raster.
    The input raster is expected to match all UMEP-expected classes but trees.
    Trees are converted to different ground types.

    Args:
        lc_path: path to directory containing land cover file(s)
        out_path: output directory
    """

    for file in glob.glob(os.path.join(lc_path, "*")):
        # print(f"file: {file}")
        if "tif" not in file:
            continue
        print(f"Considering file: {file}")
        filename = os.path.basename(file)
        # load raster
        gdal.AllRegister()
        data_set = gdal.Open(file, gdal.GA_ReadOnly)
        lcgrid = data_set.ReadAsArray().astype(float)

        lcgrid = np.where(lcgrid == 3, 6, lcgrid)  # coniferous -> bare soil
        lcgrid = np.where(lcgrid == 4, 5, lcgrid)  # decidouos -> grass

        output_location = os.path.join(out_path, filename)

        saveraster(data_set, output_location, lcgrid)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--lc_path", help="Path to landcover files")
    parser.add_argument("--out_path", help="Path to output adjusted lc files.")

    args = vars(parser.parse_args())
    if not os.path.exists(args["out_path"]):
        os.makedirs(args["out_path"])
    main(args["lc_path"], args["out_path"])
