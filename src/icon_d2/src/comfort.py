"""
Calculate thermal comfort indices for the input NWPs.

Save the output in a netCDF file in the same dir as the NWPs.
"""

import numpy as np
import xarray as xr
from pythermalcomfort import models

ATTRIBUTES = {
    "at": {
        "long_name": "Apparent Temperature",
        "short_name": "AT",
        "units": "°C"
    },
    "di": {
        "long_name": "Discomfort Index",
        "short_name": "DI",
        "units": "°C"
    },
    "humidex": {
        "long_name": "Humidity Index",
        "short_name": "Humidex",
        "units": "°C"
    },
    "utci": {
        "long_name": "Universal Thermal Climate Index",
        "short_name": "UTCI",
        "units": "°C",
    },
}


def _calc_at(tdb, rh, v, q):
    """Calculate Apparent Temperature"""
    return xr.apply_ufunc(models.at, tdb, rh, v, q, vectorize=True).rename("at")


def _calc_di(tdb, rh):
    """Calculate Discomfort Index"""
    # `discomfort_index` returns a dictionary with two items, the heat index value
    # (float) and the category (string). Xarray can't handle this. Hence, we extract
    # only the heat index value. This issue affects the `humidex` function as well.
    func = lambda tdb, rh: models.discomfort_index(tdb, rh)["di"]
    return xr.apply_ufunc(func, tdb, rh, vectorize=True).rename("di")


def _calc_humidex(tdb, rh):
    """Calculate Humidex"""
    func = lambda tdb, rh: models.humidex(tdb, rh)["humidex"]  # See why above.
    return xr.apply_ufunc(func, tdb, rh, vectorize=True).rename("humidex")


def _calc_utci(tdb, tr, v, rh):
    """Calculate utci"""
    return xr.apply_ufunc(models.utci, tdb, tr, v, rh, vectorize=True).rename("utci")


def calc_indices(nwp: dict) -> xr.Dataset:
    """Calculate thermal comfort indices for the input NWPs."""

    arr = nwp["data"]

    tdb = arr["2t"] - 273.5  # °C
    tr = arr["2t"] - 273.5  # °C  TODO: replace with actual MRT!!!
    rh = arr["2r"]  # %
    # limit rh values to 100, some might be >100 in the 4th digit maybe due to number representation issues
    rh[np.where(rh > 100)] = 100
    v = arr["wind_speed"]  # m/s

    comfort_indices = {}

    try:
        q = arr["asob_s"]  # W/m2
        comfort_indices["at"] = _calc_at(tdb, rh, v, q).assign_attrs(**ATTRIBUTES["at"])
    except KeyError:
        print("Warning: 'asob_s' was not found as a key in the given nwp, skipping 'Apparent Temperature' index.")

    comfort_indices["di"] = _calc_di(tdb, rh).assign_attrs(**ATTRIBUTES["di"])
    comfort_indices["humidex"] = _calc_humidex(tdb, rh).assign_attrs(
        **ATTRIBUTES["humidex"]
    )
    comfort_indices["utci"] = _calc_utci(tdb, tr, v, rh).assign_attrs(
        **ATTRIBUTES["utci"]
    )

    comfort_indices = xr.merge(comfort_indices.values(), compat="identical")
    comfort_indices.to_netcdf(
        nwp["dir"] / f"""nwp-{nwp["date"]}-{nwp["run"]}-thermalcomfort.nc"""
    )

    return comfort_indices
