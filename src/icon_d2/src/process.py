"""
Various functions for post-processing the NWP data.
"""

import os
import subprocess
import tempfile

import numpy as np
import xarray as xr

# An ASCII file containing the geographical coordinates
# of Dortmund's administrative boundary in WGS84.
package_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DO_ADMIN_BOUNDARY = os.path.join(package_dir, "utils", "DO_coordinates.txt")


def combine_wind_components(nwp: dict) -> dict:
    """Calculate wind speed and direction."""

    u_10m = nwp["data"]["10u"]
    v_10m = nwp["data"]["10v"]

    savedir = nwp["dir"]
    date = nwp["date"]
    run = nwp["run"]

    wind_variables = {
        "wind_speed": {
            "func": lambda u, v: np.sqrt(u**2 + v**2),
            "attrs": {
                "standard_name": "wind_speed",
                "long_name": "10 metre wind speed",
                "units": u_10m.units,
                "param": u_10m.param,
            },
        },
        "wind_dir": {
            # see https://confluence.ecmwf.int/pages/viewpage.action?pageId=133262398
            "func": lambda u, v: np.mod(180 + np.rad2deg(np.arctan2(u, v)), 360),
            "attrs": {
                "standard_name": "wind_dir",
                "long_name": "10 metre wind direction",
                "units": "degrees",
                "param": u_10m.param,
            },
        },
    }

    for wind_var in wind_variables:

        func = wind_variables[wind_var]["func"]
        attrs = wind_variables[wind_var]["attrs"]

        nwp["data"][wind_var] = func(u_10m, v_10m)
        nwp["data"][wind_var].assign_attrs(attrs)
        nwp["data"][wind_var].to_netcdf(savedir / f"nwp-{date}-{run}-{wind_var}.nc")

    return nwp


def calc_city_means(nwp: dict):
    """Aggregate the NWP data to city level.

    Step 1:
    The function masks the NWP data and keeps only the grid
    cells that are inside Dortmund's administrative boundary.

    Step 2:
    It then merges the masked netCDFs into a single xarray dataset
    and calculates the mean values for each variable as a funtion of
    time.
    """

    masked_data = []
    parent = None

    with tempfile.TemporaryDirectory() as tempdir:

        # Step 1: Mask the NWP data
        for ncfile in nwp["dir"].glob("*.nc"):

            ncfile_in = str(ncfile)
            ncfile_out = f"{tempdir}/{ncfile.stem}_masked.nc"

            try:
                subprocess.call(
                    ["cdo", f"-maskregion,{DO_ADMIN_BOUNDARY}", ncfile_in, ncfile_out]
                )
            except subprocess.CalledProcessError as err:
                print(err.output)

            da = xr.open_dataarray(ncfile_out)

            try:
                masked_data.append(da.squeeze(dim="height", drop=True))
            except KeyError:
                masked_data.append(da)
            parent = ncfile.parent

        # Step 2: Calculate the mean values
        masked_data = xr.combine_by_coords(masked_data)

        city_means = masked_data.mean(dim=["lat", "lon"], skipna=True)

        df = city_means.to_dataframe()

        if parent is not None:
            df.to_csv(parent / "city_means.csv")
        else:
            raise SystemExit("No nc files found.")

        return df
