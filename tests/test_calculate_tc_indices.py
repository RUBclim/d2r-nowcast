"""
This script tests the thermal comfort index calculation tool.

Functions:
- test_calculate_utci: Tests that the generated UTCI raster has the expected properties.
- test_calculate_pet: Tests that the generated PET raster has the expected properties.
"""

import os
from pathlib import Path

import numpy as np
from osgeo import gdal

from src.umep_wrapper.calculate_tc_indices import calculate_index_for_file

from .test_utils import clear_tmp_dir, create_dummy_metfile, create_dummy_raster

save_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tmp")
gdal.UseExceptions()

def test_calculate_utci():
    """
    Tests calculation of UTCI
    """
    clear_tmp_dir(save_dir)

    index = "UTCI"
    tmrt_path = create_dummy_raster(save_dir, "DO_MRT_2024_234_12_v0.7.0.tif", value=30.0)
    tair_path = create_dummy_raster(save_dir, "dummy_ta_raster.tif", value=25.0)
    rh_path = create_dummy_raster(save_dir, "dummy_rh_raster.tif", value=95.0)

    metfile = create_dummy_metfile(save_dir, "dummy_metfile.txt")

    calculate_index_for_file(
        index=index,
        input_tmrt=tmrt_path,
        input_tair=tair_path,
        input_rh=rh_path,
        input_wind=None,
        metfile=metfile,
        output_dir=save_dir,
    )

    # the output_filename is derived in the same way as in calculate_tc_indices
    _, basename = os.path.split(tmrt_path)
    file_suffix = "_".join(Path(basename).stem.split("_")[2:])

    variable = "UTCI" if "UTCI" in index else "PET"
    output_file_name = "DO_" + variable + "_" + file_suffix + ".tif"

    output_path = os.path.join(save_dir, output_file_name)

    assert os.path.exists(output_path), "Output file with this name should be created."

    ref = gdal.Open(tmrt_path)
    ref_arr = np.array(ref.GetRasterBand(1).ReadAsArray())
    gen = gdal.Open(output_path)
    gen_arr = np.array(gen.GetRasterBand(1).ReadAsArray())

    assert (
        gen_arr.shape == ref_arr.shape
    ), "Output resolution and shape should match input."


def test_calculate_pet():
    """
    Tests calculation of PET
    """
    clear_tmp_dir(save_dir)

    index = "PET"
    tmrt_path = create_dummy_raster(save_dir, "DO_MRT_2024_234_12_v0.7.0.tif", value=30.0)
    tair_path = create_dummy_raster(save_dir, "dummy_ta_raster.tif", value=25.0)
    rh_path = create_dummy_raster(save_dir, "dummy_rh_raster.tif", value=95.0)

    metfile = create_dummy_metfile(save_dir, "dummy_metfile.txt")

    calculate_index_for_file(
        index=index,
        input_tmrt=tmrt_path,
        input_tair=tair_path,
        input_rh=rh_path,
        input_wind=None,
        metfile=metfile,
        output_dir=save_dir,
    )

    # the output_filename is derived in the same way as in calculate_tc_indices
    _, basename = os.path.split(tmrt_path)
    file_suffix = "_".join(Path(basename).stem.split("_")[2:])
    # derive output filename from basename
    variable = "UTCI" if "UTCI" in index else "PET"
    output_file_name = "DO_" + variable + "_" + file_suffix + ".tif"
    output_file_name = "DO_" + variable + "-class_" + file_suffix + ".tif"

    output_path = os.path.join(save_dir, output_file_name)

    assert os.path.exists(output_path), "Output file with this name should be created."

    ref = gdal.Open(tmrt_path)
    ref_arr = np.array(ref.GetRasterBand(1).ReadAsArray())
    gen = gdal.Open(output_path)
    gen_arr = np.array(gen.GetRasterBand(1).ReadAsArray())

    assert (
        gen_arr.shape == ref_arr.shape
    ), "Output resolution and shape should match input."
