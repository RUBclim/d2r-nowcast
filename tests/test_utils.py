"""
This script holds some utility and helper functions for the tests.

Functions:
- clear_tmp_dir
- create_dummy_metfile
- create_dummy_metfile_48_hours
- create_dummy_metfile_dayswitch
- create_dummy_raster
- create_preprocessed_folder
- create_dummy_city_means
"""

import json
import os
import shutil
import zipfile

from osgeo import gdal, osr

MET_HEADER = "iy id it imin qn qh qe qs qf U RH Tair pres rain kdown snow ldown fcld Wuh xsmd lai kdiff kdir wdir"
MET_DUMMY_OBS = "-999 -999 -999 -999 -999 10.0 10.0 10.0 -999 0.0 10.0 -999 -999 -999 -999 -999 -999 10.0 10.0 -999"


gdal.UseExceptions()

def clear_tmp_dir(save_dir):
    """Clears all existing files from the given save_dir."""
    # Clear Output Dir
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    else:
        # remove possible dirs and their contents
        print(f"Removing existing files from {save_dir}")
        for filename in os.listdir(save_dir):
            file_path = os.path.join(save_dir, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print(f"Failed to delete {file_path}. Reason: {e}")


def create_dummy_metfile(save_dir, filename):
    """Creates a metfile with two rows of consecutive hours."""
    row_one = "2024 234 11 0 " + MET_DUMMY_OBS + "\n"
    row_two = "2024 234 12 0 " + MET_DUMMY_OBS + "\n"
    outfn = os.path.join(save_dir, filename)
    with open(outfn, "w") as file:
        file.write(MET_HEADER + "\n")
        file.write(row_one)
        file.write(row_two)
    return outfn


def create_dummy_metfile_48_hours(save_dir, filename):
    """Creates a mefile with 48 consecutive hours, starting with 12:00."""
    with open(os.path.join(save_dir, filename), "w") as file:
        file.write(MET_HEADER + "\n")
        hours = list(range(12, 24)) + list(range(0, 24)) + list(range(0, 13))
        doy = [str(233)] * 12 + [str(234)] * 24 + [str(235)] * 13
        for i, hour in enumerate(hours):
            row_dummy = f"2024 {doy[i]} {hour} 0 " + MET_DUMMY_OBS + "\n"
            file.write(row_dummy)


def create_dummy_metfile_dayswitch(save_dir, filename):
    """
    Creates a metfile with 48 consecutive hours, starting with 18:00. This
    file has a day switch right after the 6-hours warm up phase of ICON-D2,
    which is used and expected for the modelled times 00:00-02:00.
    """
    with open(os.path.join(save_dir, filename), "w") as file:
        file.write(MET_HEADER + "\n")
        hours = list(range(18, 24)) + list(range(0, 24)) + list(range(0, 19))
        doy = [str(233)] * 6 + [str(234)] * 24 + [str(235)] * 19
        for i, hour in enumerate(hours):
            row_dummy = f"2024 {doy[i]} {hour} 0 " + MET_DUMMY_OBS + "\n"
            file.write(row_dummy)


def create_dummy_raster(save_dir, filename, value=5.0) -> None:
    """Creates a dummy raster at given location."""

    driver = gdal.GetDriverByName("GTiff")

    spatref = osr.SpatialReference()
    spatref.ImportFromEPSG(25832)
    wkt = spatref.ExportToWkt()

    outfn = os.path.join(save_dir, filename)
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    with open(
        os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "test_data/dummy_raster_description/dummy_raster_description.json",
        ),
        "r",
    ) as f:
        desc = json.load(f)

    dtype = gdal.GDT_Float64

    xsize = abs(int((desc["xmax"] - desc["xmin"]) / desc["xres"]))
    ysize = abs(int((desc["ymax"] - desc["ymin"]) / desc["yres"]))

    ds = driver.Create(
        outfn,
        xsize,
        ysize,
        desc["nbands"],
        dtype,
        options=["COMPRESS=LZW", "TILED=YES"],
    )
    ds.SetProjection(wkt)
    ds.SetGeoTransform([desc["xmin"], desc["xres"], 0, desc["ymax"], 0, desc["yres"]])
    ds.GetRasterBand(1).Fill(value)
    ds.GetRasterBand(1).SetNoDataValue(desc["nodata"])
    return outfn


def create_preprocessed_folder(save_dir, tile_id):
    """Creates a folder with dummy preprocessed data for the SOLWEIG run on a tile."""
    tile_dir = os.path.join(save_dir, tile_id)
    svf_dir = os.path.join(tile_dir, "svfs")
    os.makedirs(svf_dir)

    for suffix in [
        "",
        "N",
        "S",
        "E",
        "W",
        "veg",
        "Nveg",
        "Sveg",
        "Eveg",
        "Wveg",
        "aveg",
        "Naveg",
        "Saveg",
        "Eaveg",
        "Waveg",
    ]:
        create_dummy_raster(svf_dir, f"svf{suffix}.tif")

    with zipfile.ZipFile(os.path.join(tile_dir, "svfs.zip"), "w") as file:
        for a in os.listdir(svf_dir):
            file.write(
                filename=os.path.join(svf_dir, a),
                arcname=a,
                compress_type=zipfile.ZIP_DEFLATED,
            )

    create_dummy_raster(tile_dir, f"SkyViewFactor_{tile_id}.tif")
    create_dummy_raster(tile_dir, f"wall_aspect_{tile_id}.tif")
    create_dummy_raster(tile_dir, f"wall_height_{tile_id}.tif")


def create_dummy_city_means(save_dir, filename):
    """Creates a dummy city means file which could be a result from an ICON-D2 download."""
    header = "time,10u,10v,2r,2t,ASOB_S,ASWDIFD_S,ASWDIR_S,tp,wind_dir,wind_speed\n"

    with open(os.path.join(save_dir, filename), "w") as file:
        file.write(header)
        hours = list(range(12, 23)) + list(range(0, 23)) + list(range(0, 12))
        day = [str(20)] * 12 + [str(21)] * 24 + [str(22)] * 13
        for i, hour in enumerate(hours):
            row_dummy = f"2024-08-{day[i]} {hour}:00:00,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0\n"
            file.write(row_dummy)
