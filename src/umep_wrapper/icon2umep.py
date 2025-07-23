"""
This converter is based on a developed mapping between ICON-D2 parameter and
those parameters required for SOLWEIG from the UMEP toolbox by Lindberg et al.
Since the UMEP toolbox build upon meteorogical data format created by SUEWS,
the formatter to create SUEWS-consistent data files was used as a reference.
https://github.com/UMEP-dev/SUEWS/blob/b1ca34b8f1bd4275e915fdc5b7cd7b8e5139c269/src/supy/supy/util/_era5.py#L799
"""

import argparse
import os
from datetime import datetime

import numpy as np
import pandas as pd

# MAPPING OF ICON-D2 PARAMETERS TO UMEP-SOLWEIG ACCEPTED PARAMETERS
# ICON-D2 has two names for its model parameters,
# one external for accessing the GRIB files and one used internally to name
# the datasets the following parameter mapping is in the form:
# "icon-extern": {"icon-intern", "umep"}
# NOTE: most mapped parameters are handled in the same unit
# 2m air temp has to be transformed from degree Kelvin to degree Celsius
# barometric pressure has to be transformed from Pa to hPa

# NOTE: Since a validation study from 2021 showed that ICON underestimates
# the barometric pressure (surface pressure and mean sea level pressure)
# we decided rely to the SOLWEIG deafault of 1013 hPa, which is set internally
# when the 'pres' field is not set (i.e. has a value of -999)
# Reference:
# Verification of ICON in Limited Area Mode at COSMO National
# Meteorological Services, D. Rieger et al, DOI: 10.5676/DWD_pub/nwv/icon_006

icon2umep = {
    "relhum_2m": {"intern": "2r", "umep": "RH"},
    "t_2m": {"intern": "2t", "umep": "Tair"},
    "wind_speed": {"intern": "wind_speed", "umep": "U"},
    "tot_prec": {"intern": "tp", "umep": "rain"},
    # "ps": {"inter":"sp", "umep":"pres"},
    "ASWDIFD_S": {"intern": "ASWDIFD_S", "umep": "kdiff"},
    "ASWDIR_S": {"intern": "ASWDIR_S", "umep": "kdir"},
}
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
time_converter = lambda t: datetime.strptime(t, DATE_FORMAT)


def calc_step_values(dataseries) -> np.array:
    """
    Calculates hourly steps from accumulated radiation
    values given as as 'average since model start'.
    Adds these as new column '{column}_step' to given df.

    Args:
        dataseries: 1D list or array with data points

    Returns:
        np.array with derived hourly step data

    """
    step_values = []
    for i, value in enumerate(dataseries):
        if i == 0:
            step_values.append(value)
        else:
            # regain hourly summand from overall average
            entry = value * i - sum(step_values[0:i])
            step_values.append(entry)
    return np.array(step_values)


def citymeans2umep(means_file: str, output_file: str, output_dir="./"):
    """
    Converts ICON-D2 derived city means to UMEP expected format
    """

    means_df = pd.read_csv(means_file)

    # Initialize full SUEWS/UMEP parameter dict with default values (-999)
    data_dict = {
        "iy": -999,  # Index of year, i.e. the year [YYYY]
        "id": -999,  # Index of day, i.e. day of year 1-based numbering
        "it": -999,  # Index of time, i.e. the hour 0-based
        "imin": -999,  # Index of minute, i.e. the minute 0-based
        "qn": -999,  # Net all-wave radiation [W/m^2]
        "qh": -999,  # Sensible heat flux [W/m^2]
        "qe": -999,  # Latent heat flux [W/m^2]
        "qs": -999,  # Storage heat flux [W/m^2]
        "qf": -999,  # Anthropogenic heat flux [W/m^2]
        "U": -999,  # Wind speed [m/s], for UMEP at 10m
        "RH": -999,  # Relative humidity [%]
        "Tair": -999,  # Air temperature [°C]
        "pres": -999,  # Barometric pressure [hPa]
        "rain": -999,  # Rainfall [mm]
        "kdown": -999,  # Incoming shortwave radiation [W/m^2]
        "snow": -999,  # Snow cover fraction, range 0-1
        "ldown": -999,  # Incoming longwave radiation [W/m^2]
        "fcld": -999,  # Cloud fraction [tenth]
        "Wuh": -999,  # External water use [m^3]
        "xsmd": -999,  # Observed soil moisture [m^3/m^3] or [kg/kg]
        "lai": -999,  # Observed leaf area index [m^2/m^2]
        "kdiff": -999,  # Diffuse shortwave radiation [W/m^2]
        "kdir": -999,  # Direct shortwave radiation [W/m^2]
        "wdir": -999,  # Wind direction [degree]
    }

    # Take timestamp from input
    data_dict["iy"] = [time_converter(t).year for t in means_df["time"]]
    data_dict["id"] = [time_converter(t).timetuple().tm_yday for t in means_df["time"]]
    data_dict["it"] = [time_converter(t).hour for t in means_df["time"]]
    # As SOLWEIG takes hourly values and ICON-D2 only offers hourly resolution:
    data_dict["imin"] = [0 for t in means_df["time"]]

    # Map parameters
    # NOTE: the values are round to 2 digits with numpy.round() function
    for key, value in icon2umep.items():
        data_dict[value["umep"]] = means_df[value["intern"]].to_numpy()
        # Convert 'Temperature at 2m above ground' from Kelvin to Celsius
        if key == "t_2m":
            data_dict[value["umep"]] -= 273.15
        # # Convert 'Surface pressure (not reduced)' from Pa to hPa
        # if key == "ps":
        #     data_dict[value["umep"]] /= 100

        data_dict[value["umep"]] = data_dict[value["umep"]].round(
            2
        )  # pylint: disable=no-member

    # Derive stepwise, hourly radiation for both radiation components
    default_value = (
        0.001  # if ICON indicates negative radiation, 0 might lead to artifacts
    )

    # Note: ICON-D2 radiation values are 'averaged since model start'
    # derive hourly steps of radiation values
    kdiff_step = calc_step_values(data_dict["kdiff"])
    kdir_step = calc_step_values(data_dict["kdir"])
    data_dict["kdiff"] = np.where(kdiff_step < 0, default_value, kdiff_step)
    data_dict["kdir"] = np.where(kdir_step < 0, default_value, kdir_step)

    # Derive incoming global shortwave radiation from diffuse and direct components
    data_dict["kdown"] = data_dict["kdiff"] + data_dict["kdir"]

    # and crop negative values (values < 0 not plausible)
    data_dict["kdown"] = np.where(
        data_dict["kdown"] < 0, default_value, data_dict["kdown"]
    )

    # Round to 2 digits, as umep expects it
    data_dict["kdown"] = data_dict["kdown"].round(2)  # pylint: disable=no-member
    data_dict["kdiff"] = data_dict["kdiff"].round(2)  # pylint: disable=no-member
    data_dict["kdir"] = data_dict["kdir"].round(2)  # pylint: disable=no-member

    # save to CSV by utilizing pandas
    df = pd.DataFrame(data_dict)
    # indexing from SUEWS
    df = df.astype({"iy": "int32", "id": "int32", "it": "int32", "imin": "int32"})
    df.set_index(["iy", "id", "it", "imin"])
    filename = os.path.join(output_dir, output_file)
    df.to_csv(filename, sep=" ", index=False)
    # print(f"Wrote file to {output_dir}{output_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="A tool to convert ICON-D2 city-avergaged hourly data to UMEP accepted format"
    )
    parser.add_argument(
        "--city_means_file", help="Path to city_means.csv, that should be used."
    )
    parser.add_argument("--output_file", help="Name of the output file.")
    parser.add_argument(
        "--output_dir", help="Output directory, default './'", required=False
    )

    arg_dict = vars(parser.parse_args())

    citymeans2umep(
        means_file=arg_dict.get("city_means_file"),
        output_file=arg_dict.get("output_file"),
        output_dir=arg_dict.get("output_dir") or "./",
    )
