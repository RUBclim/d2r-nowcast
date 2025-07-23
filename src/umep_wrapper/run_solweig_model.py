"""
This file conducts the solweig processing for a single setup.
"""

import argparse
import logging
import os
import time

import yaml

# imports from umep_processing_fork packages
from processor.solweig_algorithm_standalone import ProcessingSOLWEIGAlgorithm

logger = logging.getLogger(__name__)
FORMAT = "[%(filename)s:%(lineno)s - %(funcName)20s()  %(name)s ] %(message)s"
logger.setLevel(logging.WARNING)


def main(args_dict: dict):
    """
    parses script arguments and runs solweig

    Args:
        args_dict: a dictionary with solweig run arguments

    Returns: solweig return value

    """
    data_path = args_dict["data_path"]
    if not os.path.exists(data_path):
        logger.warning("Data path '%s' does not exist.", data_path)
        return None
    os.environ["DATA_PATH"] = data_path
    logger.debug("ENVIRONMENT VARIABLES:\n %s", str(os.environ))
    logger.debug(os.environ["PROJ_LIB"])
    config_file = args_dict["config_file"]
    met_file_path = None
    svfs_path = None
    cdsm_path = None
    out_dir = None

    # parse optional arguments
    if args_dict["met_file_path"] is not None:
        met_file_path = args_dict["met_file_path"]

    if args_dict["svfs_path"] is not None:
        svfs_path = args_dict["svfs_path"]

    if args_dict["cdsm_path"] is not None:
        cdsm_path = args_dict["cdsm_path"]

    if args_dict["out_dir"] is not None:
        out_dir = args_dict["out_dir"]

    return run_solweig(
        config_file=config_file,
        met_file_path=met_file_path,
        svfs_path=svfs_path,
        cdsm_path=cdsm_path,
        out_dir=out_dir,
    )


def run_solweig(
    config_file: str,
    met_file_path: str = None,
    svfs_path: str = None,
    cdsm_path: str = None,
    out_dir: str = None,
):
    """
    Args:
        config_file: path to solweig configuration file
        met_file_path: path to metfile
        svfs_path: path to svf zip folder
        cdsm_path: path to CDSM file
        out_dir: path to where the results should be output

    Returns: paths to results, OUTPUT_CDSM and OUTPUT_POINTFILE

    """

    logger.info("solweig start")
    start_time = time.time()

    # RUN
    algo = ProcessingSOLWEIGAlgorithm()
    algo.initAlgorithm()

    solweig_config = load_solweig_config(config_file)

    # overwrite existing default paths
    if met_file_path is not None:
        solweig_config["INPUTMET"] = met_file_path
    if svfs_path is not None:
        solweig_config["INPUT_SVF"] = svfs_path
    if out_dir is not None:
        solweig_config["OUTPUT_DIR"] = out_dir
    if cdsm_path is not None:
        solweig_config["INPUT_CDSM"] = cdsm_path

    if not os.path.exists(solweig_config["OUTPUT_DIR"]):
        os.makedirs(solweig_config["OUTPUT_DIR"])

    logger.info("Run Solweig.processAlgorithm")
    out_dict = algo.processAlgorithm(solweig_config)
    out_dict["POI_FILE"] = solweig_config["POI_FILE"]
    end_time = time.time()
    logger.info("RUNTIME: %f s", end_time - start_time)
    return out_dict, end_time - start_time


def load_solweig_config(solweig_config_file: str):
    """loads solweig configuration from a yaml file

    Args:
        solweig_config_file (string): path to solweig config file

    Returns:
        a configuration dictionary
    """
    with open(solweig_config_file, "r") as file:
        solweig_config = yaml.safe_load(os.path.expandvars(file.read()))

    return solweig_config


if __name__ == "__main__":
    # Variant A: run solweig directly
    # run_solweig("solweig_parameter.yaml")

    # Variant B: argument parsing
    parser = argparse.ArgumentParser()
    parser.add_argument("--proj_lib", help="Path to folder that contains proj.db")
    parser.add_argument("--data_path", help="System Path to where the data is stored")
    parser.add_argument("--config_file", help="Path to solweig configuration file")
    parser.add_argument(
        "--met_file_path", help="Path to meteorological data file, ERA5 format required"
    )
    parser.add_argument("--svfs_path", help="Path to svf zip folder")
    parser.add_argument("--cdsm_path", help="Path to CDSM file")
    parser.add_argument("--out_dir", help="Path to where the results should be output")

    args = vars(parser.parse_args())
    print(args)

    os.environ["PROJ_LIB"] = os.path.abspath(args["proj_lib"])

    main(args)
