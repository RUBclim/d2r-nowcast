"""Calculate Indices (UTCI and PET) for 2d Data Arrays (Tmrt Maps + weather data)"""

import argparse
import os
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
from osgeo import gdal
from thermal_comfort import pet_static, utci_approx

# import utility script from relativ path for script execution
libPath = "../../utils"
if not libPath in sys.path:
    sys.path.append(libPath)
from utils.save_raster import saveraster

gdal.UseExceptions()

# A 'default person' given by the DWD
# https://www.dwd.de/DE/service/lexikon/Functions/glossar.html?lv3=101438&lv2=101334
# clothing from SOLWEIG default value
KLIMA_MICHEL = SimpleNamespace(
    mbody=75,  # body mass (kg)
    age=35,  # person's age (years)
    height=1.75,  # height (meters)
    activity=135,  # activity level (W)
    sex=1,  # 1=male 2=female
    clo=0.9,  # clothing amount (0-5)
)
MET_FACTOR = 58.2

NO_DATA_VALUE = -32768.0

# UTCI Assessment Scale, G. Jendritzky
# Glossary of Terms for Thermal Physiology (2003). Journal of Thermal Biology 28, 75-106
UTCI_MAP = {
    -32767.0: -32768,  # handle nan(=NO_DATA_VALUE, right exclusive limits)
    -40.0: 0,  # "extreme cold stress",
    -27.0: 1,  # "very strong cold stress",
    -13.0: 2,  # "strong cold stress",
    0.0: 3,  # "moderate cold stress",
    9.0: 4,  # "slight cold stress",
    26.0: 5,  # "no thermal stress",
    32.0: 6,  # "moderate heat stress",
    38.0: 7,  # "strong heat stress",
    46.0: 8,  # "very strong heat stress",
    1000.0: 9,  # "extreme heat stress",
}

# PET from Matzarakis et al. 1999
PET_MAP = {
    -32767.0: -32768,  # handle nan(=NO_DATA_VALUE, right exclusive limits)
    4.0: 0,  # "extreme cold stress",
    8.0: 1,  # "strong cold stress",
    13.0: 2,  # "moderate cold stress",
    18.0: 3,  # "slight cold stress",
    23.0: 4,  # "no thermal stress",
    29.0: 5,  # "slight thermal stress",
    35.0: 6,  # "moderate heat stress",
    41.0: 7,  # "strong heat stress",
    1000.0: 8,  # "extreme heat stress",
}

ATMOSPHERIC_PRESSURE = 1013.0  # SOLWEIG default pressure


# From pythermalcomfort mapping
def mapping(value, map_dictionary, right=True):
    """Maps a temperature array to stress categories.

    Parameters
    ----------
    value : float, array-like
        Temperature to map.
    map_dictionary: dict
        Dictionary used to map the values
    right: bool, optional
        Indicating whether the intervals include the right or the left bin edge.

    Returns
    -------
    Stress category for each input temperature.
    """
    bins = np.array(list(map_dictionary.keys()))
    words = np.array(
        list(map_dictionary.values())
    )  # np.append(np.array(list(map_dictionary.values())), "unknown")
    return words[np.digitize(value, bins, right=right)]


def calculate_index_for_file(
    index: str,
    input_tmrt: str,
    input_tair: str,
    input_rh: str,
    metfile: str,
    output_dir: str,
    input_wind: str = None,
    also_save_class_raster: bool = True,
):
    """
    Calculates Index maps for a single Tmrt file, matching wind field file and a given
    weather data file

    Args:
        index (str): 'PET' or 'UTCI'
        input_tmrt (str): path to input directory containing tmrt raster
        input_tair (str): path to input directory containing tair raster in C
        input_rh (str): path to input directory containing rh raster
        metfile (str): path to meteorological data file
        output_dir (str): path to directory where to save results to
        input_wind (str): path to input directory containing wind speed raster
        also_save_class_raster (bool): whether to also save raster as classified raster
    """
    print("calculate_index_for_file")
    df = pd.read_csv(metfile, sep=" ")

    tmp = Path(input_tmrt).stem.split("_")
    try:
        year = int(tmp[-4])
    except ValueError:
        print(
            "Wrong file naming pattern. Expected pattern 'DO_VAR_YYYY_DOY_HH_vX.X.X.tif'"
        )
        sys.exit(1)

    doy = int(tmp[-3])
    hour = int(tmp[-2])
    entry = df[(df["iy"] == year) & (df["id"] == doy) & (df["it"] == hour)]

    # in case data is finer than in hourly resolution, only the first entry is used
    selected_entry = entry.iloc[0]

    raster = gdal.Open(input_tmrt, gdal.GA_ReadOnly)
    tmrt_raster = raster.ReadAsArray()  # read(1)

    # replace NO_DATA_VALUE with nan
    tmrt_raster[tmrt_raster == NO_DATA_VALUE] = np.nan

    rows = tmrt_raster.shape[0]
    cols = tmrt_raster.shape[1]

    # read raster data
    if input_tair is not None:
        tair_raster = gdal.Open(input_tair, gdal.GA_ReadOnly).ReadAsArray()
        tair_raster[tair_raster == NO_DATA_VALUE] = np.nan
    else:
        tair_raster = np.ones((rows, cols)) * selected_entry["Tair"]
    if np.nanmean(tair_raster) > 100:
        print(
            "WARNING: Air Temperature might be given in K instead of C. Please correct."
        )

    if input_rh is not None:
        rh_raster = gdal.Open(input_rh, gdal.GA_ReadOnly).ReadAsArray()
        rh_raster = np.clip(rh_raster, 0, 100)
        rh_raster[rh_raster == NO_DATA_VALUE] = np.nan
    else:
        rh_raster = np.ones((rows, cols)) * selected_entry["RH"]

    if input_wind is not None:
        windspeed_10m_raster = gdal.Open(input_wind, gdal.GA_ReadOnly).ReadAsArray()
    else:
        windspeed_10m_raster = np.ones((rows, cols)) * selected_entry["U"]

    pressure_raster = np.ones((rows, cols)) * ATMOSPHERIC_PRESSURE

    # retrieve the initial shape
    orig_shape = tair_raster.shape

    # reshape arrays to be 1-dimensional
    tair_raster = np.ravel(tair_raster)
    tmrt_raster = np.ravel(tmrt_raster)
    windspeed_10m_raster = np.ravel(windspeed_10m_raster)
    rh_raster = np.ravel(rh_raster)
    pressure_raster = np.ravel(pressure_raster)

    match index:
        case "PET":
            thermal_comfort_index = pet_static(
                ta=tair_raster,
                tmrt=tmrt_raster,
                v=windspeed_10m_raster,
                rh=rh_raster,
                p=pressure_raster,
            )
        case "UTCI":
            # calculate utci
            thermal_comfort_index = utci_approx(
                ta=tair_raster, tmrt=tmrt_raster, v=windspeed_10m_raster, rh=rh_raster
            )
        case _:
            print(f"Given index '{index}' is not known. " f"Use 'PET' or 'UTCI'.")
            sys.exit(1)

    # restore the original shape
    thermal_comfort_index = thermal_comfort_index.reshape(orig_shape)

    # round index to 3 decimals
    thermal_comfort_index = np.round(thermal_comfort_index, 3)
    # replace np.nan values with NO_DATA_VALUE
    thermal_comfort_index[np.isnan(thermal_comfort_index)] = NO_DATA_VALUE

    _save_output(
        thermal_comfort_index, index, input_tmrt, output_dir, also_save_class_raster
    )


def _save_output(
    thermal_comfort_index: np.array,
    index: str,
    input_filepath: str,
    output_dir: str,
    also_save_class_raster: bool,
):
    """
    Save a raster to a filepath matching the given input filepath.

    Args:
        thermal_comfort_index (numpy array): thermal comfort raster
        index (str): 'PET' or 'UTCI'
        input_filepath (str): path to input reference raster, i.e tmrt raster
        output_dir (str): path to directory where to save results to
        also_save_class_raster (bool): whether to also save raster as classified raster
    """

    # get georeference
    gdal_tmrt_map = gdal.Open(input_filepath, gdal.GA_ReadOnly)

    # set output location and filename
    dirname, basename = os.path.split(input_filepath)
    if output_dir is not None:
        # overwrite dirname
        dirname = output_dir
        if not os.path.exists(dirname):
            print(f"Output_dir {output_dir} did not exist. Created directory.")
            os.makedirs(dirname)

    # extract file suffix
    # e.g DO_MRT_2024_093_10_v0.7.0.tif -> 2024_093_10_v0.7.0
    file_suffix = "_".join(Path(basename).stem.split("_")[2:])
    # derive output filename from basename
    variable = "UTCI" if index == "UTCI" else "PET"
    output_file_name = "DO_" + variable + "_" + file_suffix + ".tif"

    output_location = os.path.join(dirname, output_file_name)

    saveraster(gdal_tmrt_map, output_location, thermal_comfort_index)

    print(f"Saved {index} map at: {output_location}")

    if also_save_class_raster:
        if index == "UTCI":
            # Indicating whether the intervals include the right or the left bin edge.
            # [9.0, 26.0[ no thermal stress, left edge inclusive
            thermal_comfort_index_class = mapping(
                thermal_comfort_index, UTCI_MAP, right=False
            )
        else:  # "PET" in index
            thermal_comfort_index_class = mapping(
                thermal_comfort_index, PET_MAP, right=False
            )

        # derive output filename from basename
        output_file_name = "DO_" + variable + "-class_" + file_suffix + ".tif"

        output_location = os.path.join(dirname, output_file_name)

        saveraster(gdal_tmrt_map, output_location, thermal_comfort_index_class)
        print(f"Saved {index}-class map at: {output_location}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--index", help='Choose from ["PET", "UTCI"].')
    parser.add_argument("--input_tmrt", help="Full path to Tmrt input file.")
    parser.add_argument("--input_tair", help="Full path to Tair input file (in C).")
    parser.add_argument("--input_rh", help="Full path to RH input file.")
    parser.add_argument("--input_wind", help="Full path to wind input file.")
    parser.add_argument("--metfile", help="Full path to meteorological data file.")
    parser.add_argument(
        "--output_dir", help="Full path to output directory to store the result."
    )

    args = vars(parser.parse_args())

    print("Calculating thermal comfort index ..")

    calculate_index_for_file(
        index=args["index"],
        input_tmrt=args["input_tmrt"],
        input_tair=args["input_tair"],
        input_rh=args["input_rh"],
        input_wind=args["input_wind"],
        metfile=args["metfile"],
        output_dir=args["output_dir"],
    )
