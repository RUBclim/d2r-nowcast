"""
This file conducts the solweig pre-processing for sky view factor and wall descriptors.
"""

import argparse
import os
import sys
import time

import yaml

# imports from umep_processing_fork packages
from preprocessor.skyviewfactor_algorithm_standalone import (
    ProcessingSkyViewFactorAlgorithm,
)
from preprocessor.wall_heightaspect_algorithm_standalone import (
    ProcessingWallHeightAscpetAlgorithm,
)


def run_wall_height_aspect_calculator(
    config_file: str,
):
    """
    Returns: Path to results
    """
    start_time = time.time()

    algo = ProcessingWallHeightAscpetAlgorithm()
    algo.initAlgorithm()

    wall_heightaspect_config = load_config(config_file)

    # make output dirs if not existing
    output_dir = os.path.dirname(wall_heightaspect_config["OUTPUT_HEIGHT"])
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"created directory {output_dir}")

    output_file = algo.processAlgorithm(wall_heightaspect_config)

    end_time = time.time()
    return output_file, end_time - start_time


def run_svf_calculator(config_file: str, cdsm_path: str = None):
    """

    Returns: paths to results, OUTPUT_CDSM and OUTPUT_POINTFILE

    """
    start_time = time.time()

    # RUN
    algo = ProcessingSkyViewFactorAlgorithm()
    algo.initAlgorithm()

    svf_config = load_config(config_file)

    if cdsm_path is not None:
        svf_config["INPUT_CDSM"] = cdsm_path

    # ensure target directories
    if not os.path.exists(svf_config["OUTPUT_DIR"]):
        os.makedirs(svf_config["OUTPUT_DIR"])

    out_dict = algo.processAlgorithm(svf_config)
    end_time = time.time()
    return svf_config["OUTPUT_DIR"], end_time - start_time


def load_config(config_file: str):
    """loads a config dict form yaml

    Args:
        config_file (str): path to config file

    Returns:
        dict containing config
    """
    with open(config_file, "r") as file:
        config = yaml.safe_load(os.path.expandvars(file.read()))
    return config


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_path", help="System Path to where the data is stored")
    parser.add_argument("--svf_config_file", help="Path to svf configuration file")
    parser.add_argument(
        "--wall_config_file", help="Path to wall height aspect configuration file"
    )
    args_dict = vars(parser.parse_args())

    data_path = args_dict["data_path"]
    if not os.path.exists(data_path):
        print(f"Given data_path {data_path} does not exist. Please check the path.")
        sys.exit(0)
    os.environ["DATA_PATH"] = data_path
    print("data path", data_path)

    svf_config_file = args_dict["svf_config_file"]
    wall_config_file = args_dict["wall_config_file"]

    run_wall_height_aspect_calculator(wall_config_file)
    run_svf_calculator(svf_config_file)
