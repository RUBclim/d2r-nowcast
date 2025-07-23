"""This module is a helper to ingest generated rasters to the database"""

import argparse

# import tool from d2r-api repo
from app.tc_ingester import ingest_raster

version = "0.8.0"


def ingest_rasters(timestamp: str):
    """
    Ingest rasters from to database

    Note: Only works with the required .env variables set.

    Args:
        timestamp(str): Timestamp in the format YYYY_DOY_HH, e.g. 2025_090_09
    """

    raster_list = ["MRT", "UTCI", "UTCI_CLASS", "PET", "PET_CLASS", "TA", "RH"]
    raster_names = ["MRT", "UTCI", "UTCI-class", "PET", "PET-class", "TA", "RH"]

    for i, raster in enumerate(raster_list):
        path = f"/usr/src/app/rasters/{raster}/DO_{raster_names[i]}_{timestamp}_v{version}_cog.tif"
        ingest_raster.delay(
            path=path, override_path=f"/usr/src/app/data/rasters/{raster}"
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--timestamp",
        "-t",
        help="Timestamp in format: YYYY_DOY_HH to identify the rasters of the hour to shift.",
    )

    args = parser.parse_args()

    ingest_rasters(args.timestamp)
