"""
This file conducts the solweig preprocessing for all tiles in a given dataset.
Preprocessing consists of wall height and aspect raster creation for given DSM files and
sky view factor calculation for the given DSM files.
"""

import argparse
import glob
import logging
import os
import signal
import sys
from functools import partial
from logging.handlers import QueueHandler, QueueListener
from multiprocessing import Pool, Queue

import numpy as np
import psutil
from jinja2 import Environment, FileSystemLoader
from osgeo import gdal

from umep_wrapper.run_solweig_prepare import (
    run_svf_calculator,
    run_wall_height_aspect_calculator,
)

gdal.UseExceptions()


# https://stackoverflow.com/a/34964369
def worker_init(q: Queue) -> None:
    """
    Initilize worker and queue hander

    Args:
        q (Queue): a queue object to initialize the queue handler
    """

    # all records from worker processes go to qh and then into q
    qh = QueueHandler(q)
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(qh)


def logger_init(log_file_path: str) -> tuple[QueueListener, Queue]:
    """
    Initialize queue logging

    Args:
        log_file_path (str): path to logging output file
    """

    q = Queue()
    # this is the handler for all log records
    handler = logging.FileHandler(log_file_path)
    handler.setFormatter(logging.Formatter("%(asctime)s;%(msecs)d;%(message)s"))

    # ql gets records from the queue and sends them to the handler
    ql = QueueListener(q, handler)
    ql.start()

    logger = logging.getLogger("runtime_logger")
    logger.setLevel(logging.INFO)
    # add the handler to the logger so records from this process are handled
    logger.addHandler(handler)

    return ql, q


def main(args: dict[str, str]) -> None:
    """
    Run SOLWEIG preprocessing with the given settings for multiple tiles in parallel.

    Args:
        args (dict): dict with runtime variables, i.e. file paths for SOLWEIG inputs
    """

    data_dict = {}

    normalized_dsm_path = os.path.normpath(
        os.path.join(args["data_path"], args["dsm_folder"], "*")
    )

    normalized_cdsm_path = os.path.normpath(
        os.path.join(args["data_path"], args["cdsm_folder"], "*")
    )

    template_path = os.path.normpath(os.path.join(os.getcwd(), "config_templates"))
    print(template_path)

    resolution = args["dsm_folder"].split("_")[-3]
    size = args["dsm_folder"].split("_")[-1]

    solweig_process_folder = f"SOLWEIG_prepare_{resolution}_{size}"
    solweig_process_path = os.path.normpath(
        os.path.join(args["output_path"], solweig_process_folder)
    )
    if not os.path.exists(solweig_process_path):
        os.mkdir(solweig_process_path)

    log_file_path = os.path.join(
        solweig_process_path, f"solweig_preprocessing_{resolution}_{size}_log.log"
    )

    # setup logger
    logging.basicConfig(
        filename=log_file_path,
        filemode="w",
        format="%(asctime)s;%(msecs)d;%(message)s",
        datefmt="%H:%M:%S",
        level=logging.INFO,
    )
    runtime_logger = logging.getLogger("runtime_logger")
    runtime_logger.info("step;tile;runtime;cpu;vmem;vmem_all;pid")

    dsm_files = sorted(glob.glob(normalized_dsm_path))
    cdsm_files = sorted(glob.glob(normalized_cdsm_path))

    # extract filenames for further processing
    for dsm_file in dsm_files:
        if ".tif" not in dsm_file:
            continue
        dsm_file = os.path.normpath(dsm_file)
        dsm_file = dsm_file.split(os.sep)[-1]
        # DSM file naming pattern: DO_DTM+DSM_mosaic_<reso>_<y>_<x>.tif
        yx_coords = dsm_file.split(".")[0].split("_")[-2:]
        y_x = yx_coords[0] + "_" + yx_coords[1]

        matching_cdsm = [s for s in cdsm_files if y_x in s]
        assert len(matching_cdsm) == 1
        matching_cdsm = matching_cdsm[0].split(os.sep)[-1]

        data_dict[y_x] = {"dsm": dsm_file, "cdsm": matching_cdsm}

    print(
        f"Memory usage: \n"
        f"cpu [%]: {psutil.cpu_percent()}\n"
        f"vmem [%]:{psutil.virtual_memory().percent}\n"  # percentage of used RAM
        f"vmem: {psutil.virtual_memory()}"
    )  # physical memory usage

    # execute solweig and required preprocesses for each tile (k= yx coordinates)
    # for k, v in data_dict.items():
    q_listener, q = logger_init(log_file_path)

    func = partial(
        process_tile,
        args,
        template_path,
        solweig_process_folder,
        solweig_process_path,
        #    runtime_logger,
    )

    signal.signal(signal.SIGTERM, lambda signum, stack_frame: sys.exit(1))
    # maxtasksprchild set to one to contain memory issue: https://stackoverflow.com/a/54975030
    with Pool(processes=32, initializer=worker_init, initargs=[q]) as pool:
        result = pool.map_async(func, data_dict.items())
        try:
            _ = result.get()
        except Exception as e:
            print(f"Failed with {e}")
        # from https://superfastpython.com/multiprocessing-pool-map_async/
        # close the process pool
        pool.close()
        # wait for all tasks to complete and processes to close
        pool.join()

    q_listener.stop()


def process_tile(
    args: dict,
    template_path: str,
    solweig_process_folder: str,
    solweig_process_path: str,
    k_v_pair: tuple[str, dict],
):
    """
    Run SOLWEIG preprocessing for a single tile.

    Args:
        args (dict): dict with runtime variables, i.e. file paths for SOLWEIG inputs
        template_path (str): folder which contains the SOLWEIG parameter templates
        solweig_process_folder (str): folder for SOLWEIG output
        solweig_process_folder (str): location of folder for SOLWEIG output
        k_v_pair (tuple): maps tile id 'y_x' to the respective surface model tiles
    """

    os.environ["PROJ_LIB"] = args["proj_lib"]

    k, v = k_v_pair[0], k_v_pair[1]

    # print("template path", template_path)
    env = Environment(
        loader=FileSystemLoader(template_path), trim_blocks=True, lstrip_blocks=True
    )

    # 1: collect data for tile
    data = {
        "data_path": args["data_path"],
        "dsm_folder": args["dsm_folder"],
        "cdsm_folder": args["cdsm_folder"],
        "output_path": args["output_path"],
        "dsm_file": v["dsm"],
        "cdsm_file": v["cdsm"],
        "y_x": k,
        "solweig_process_folder": solweig_process_folder,
    }

    # check if dsm is outside the city's borders (whether the tile was fully masked)
    cdsm_path = os.path.join(data["data_path"], data["cdsm_folder"], data["cdsm_file"])
    cdsm_tiff = gdal.Open(cdsm_path, gdal.GA_ReadOnly).ReadAsArray()

    cdsm_values = np.asarray(cdsm_tiff)
    if (cdsm_values == np.zeros(cdsm_values.shape)).all():
        logging.info("skip;%s;-1;-1;-1;-1;%d", k, os.getpid())
        return

    # create output path for process results
    tile_output_path = os.path.normpath(os.path.join(solweig_process_path, k))
    if not os.path.exists(tile_output_path):
        os.mkdir(tile_output_path)

    if os.path.exists(os.path.join(tile_output_path, "svfs.zip")):
        print(f"SVFs exist for {k}")
        return

    # 2: run wall_calc
    # 2.a: read config file template
    template = env.get_template("wall_parameter_template.yaml")
    config_file = os.path.join(tile_output_path, f"wall_parameter_{k}.yaml")
    # 2.b: write tile specific data in template to create individual config file
    with open(config_file, "w") as file:
        file.write(template.render(data))
    # 2.c: run wall height and aspect algorithm
    output_file, runtime = run_wall_height_aspect_calculator(config_file)

    logging.info(
        f"wall;{k};{round(runtime,4)};{psutil.cpu_percent()};"
        f"{psutil.virtual_memory().percent};{psutil.virtual_memory()};{os.getpid()}"
    )

    print(f"Wall calc successful, output is: {output_file}")
    print(
        f"Memory usage: \n"
        f"cpu [%]: {psutil.cpu_percent()}\n"
        f"vmem [%]:{psutil.virtual_memory().percent}\n"  # percentage of used RAM
        f"vmem: {psutil.virtual_memory()}"
    )  # physical memory usage

    # 3: run svf calculation with config
    # 3.a: read config file template
    template = env.get_template("svf_parameter_template.yaml")
    config_file = os.path.join(tile_output_path, f"svf_parameter_{k}.yaml")
    # 3.b: write tile specific data in template to create individual config file
    with open(config_file, "w") as file:
        file.write(template.render(data))
    # 3.c: run svf algorithm
    output_file, runtime = run_svf_calculator(config_file)

    logging.info(
        f"svf;{k};{round(runtime,4)};{psutil.cpu_percent()};"
        f"{psutil.virtual_memory().percent};{psutil.virtual_memory()};{os.getpid()}"
    )

    print(f"svf calc successful, output is: {output_file}")
    print(
        f"Memory usage: \n"
        f"cpu [%]: {psutil.cpu_percent()}\n"
        f"vmem [%]:{psutil.virtual_memory().percent}\n"  # percentage of used RAM
        f"vmem: {psutil.virtual_memory()}"
    )  # physical memory usage


def check_paths(data_path: str, dsm_folder: str, cdsm_folder: str, output_path: str):
    """checks whether the required folders exists and have same resolution and size

    Args:
        data_path (str): folder which contains the required surface model and met data
        dsm_folder (str): folder of DSM files located within data_path
        cdsm_folder (str): folder of CDSM files located within data_path
        output_path (str): path to which the output will be saved

    Raises:
        FileNotFoundError: thrown if one of the folders does not exists
        RuntimeError: thrown if dtm and dsm resolution or size don't match

    """
    # check existance
    if not os.path.isdir(data_path):
        raise FileNotFoundError(f"Data path {data_path} does not exist.")
    if not os.path.isdir(os.path.join(data_path, dsm_folder)):
        raise FileNotFoundError(
            f"DSM folder {dsm_folder} does not exist within data folder {data_path}."
        )
    if not os.path.isdir(os.path.join(data_path, cdsm_folder)):
        raise FileNotFoundError(
            f"CDSM folder {cdsm_folder} does not exist within data folder {data_path}."
        )
    if not os.path.isdir(output_path):
        raise FileNotFoundError(f"Output path {output_path} does not exist.")

    # check matching
    # DSM folder format: DO_DTM+DSM_mosaic_<reso>_tiles_<size>+<overlap>
    dsm_resolution = dsm_folder.split("_")[-3]
    # CDSM folder format: canopy_DSM_<reso>_tiles_<size>+<overlap>
    cdsm_resolution = cdsm_folder.split("_")[-3]

    if dsm_resolution != cdsm_resolution:
        raise RuntimeError(
            f"Resolutions of DSM and CDSM do not match: "
            f"{dsm_resolution} (DSM) vs. {cdsm_resolution}(DTM)"
        )

    dsm_size = dsm_folder.split("_")[-1]
    cdsm_size = cdsm_folder.split("_")[-1]
    if dsm_size != cdsm_size:
        raise RuntimeError(
            f"Sizes of DSM and DTM do not match: {dsm_size} (DSM) vs. {cdsm_size}(DTM)"
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--proj_lib",
        type=str,
        required=False,
        help="Path to folder that contains proj.db",
    )
    parser.add_argument(
        "--data_path", type=str, required=True, help="The path to the data folders"
    )
    parser.add_argument(
        "--dsm_folder",
        type=str,
        required=True,
        help="Name of the DSM folder, located in data_path",
    )
    parser.add_argument(
        "--cdsm_folder",
        type=str,
        required=True,
        help="Name of the CDSM folder, located in data_path",
    )
    parser.add_argument(
        "--output_path", type=str, required=True, help="Path to output folder"
    )

    args_dict = vars(parser.parse_args())

    if args_dict["proj_lib"] is not None:
        os.environ["PROJ_LIB"] = os.path.abspath(args_dict["proj_lib"])
        print("proj_lib", args_dict["proj_lib"], os.environ["PROJ_LIB"])

    check_paths(
        args_dict["data_path"],
        args_dict["dsm_folder"],
        args_dict["cdsm_folder"],
        args_dict["output_path"],
    )

    main(args_dict)
