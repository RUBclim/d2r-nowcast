"""
This script tests the successful tile-wise processing of the pipeline.

Functions:
- test_process_tile: Tests that the processing creates the expected files at the expected locations.
"""

import os

from src.umep_wrapper.solweig_multi_processing import process_tile

from .test_utils import (
    clear_tmp_dir,
    create_dummy_metfile,
    create_dummy_raster,
    create_preprocessed_folder,
)


def test_process_tile():
    """
    Tests whether the tile processing creates the expected amount of files.
    """
    data_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "test_data",
        "process_tile_test_data",
    )
    tmp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tmp")
    save_dir = os.path.join(tmp_dir, "solweig")

    clear_tmp_dir(save_dir)

    create_dummy_raster(tmp_dir, "dummy_raster.tif")
    create_dummy_metfile(tmp_dir, "metfile.txt")

    dummy_tile_id = "01_01"
    create_preprocessed_folder(
        os.path.join(tmp_dir, "preprocessed_data"), dummy_tile_id
    )

    data_path_dict = {
        "data_path": tmp_dir,
        "dsm_folder": "",
        "cdsm_folder": "",
        "dtm_folder": "",
        "preprocess_data_path": os.path.join(tmp_dir, "preprocessed_data"),
        "output_path": save_dir,
        "proj_lib": os.environ[
            "PROJ_LIB"
        ],  # IMPORTANT: set new env PROJ_LIB before running pytest
    }
    test_files = {
        "dsm": "dummy_raster.tif",
        "cdsm": "dummy_raster.tif",
        "dtm": "dummy_raster.tif",
        "lc_path": os.path.join(tmp_dir, "dummy_raster.tif"),
    }

    process_tile(
        args=data_path_dict,
        template_path=data_dir,
        normalized_metfile_path=os.path.join(tmp_dir, "metfile.txt"),
        solweig_process_folder="solweig_out",
        solweig_process_path=save_dir,
        k_v_pair=[dummy_tile_id, test_files],
    )

    assert (
        len(os.listdir(save_dir)) == 2
    ), "Output should be saved in two output folders"
    # these two folders are 1) for the filled template 2) for computational output

    counter = 0
    for entry in os.listdir(
        os.path.join(save_dir, "solweig_out", "temp_tiles", dummy_tile_id)
    ):
        if "Tmrt" in entry and ".tif" in entry:
            counter += 1

    assert counter == 3, "Should output exactly three Tmrt files (2 hours + average)."
