"""
Helper functions for D2R's interpolation module.

Functions:
- correct_invalid_rh(rh: np.ndarray) -> np.ndarray:
    Apply sanity corrections to the RH predictions.
- create_geotiff(savepath: str, arr: np.ndarray, geoTF: list, epsg: int, ndv=-9999):
    Write a numpy array to a compressed GeoTIFF file.
- create_json(savepath: str, data: dict):
    Write a dictionary to a JSON file.
- evaluate(true: np.ndarray, test: np.ndarray) -> dict:
    Compare the true values with the test values and return evaluation metrics.
- read_raster(fpath: str, ndv=-9999) -> dict:
    Read the features from a GeoTIFF file and return them as a dictionary.
- sample_raster(raster: np.ndarray, point: list) -> np.ndarray:
    Sample the raster data at the given points.
- read_geojson(fpath, vars: list) -> pd.DataFrame:
    Read a GeoJSON file with biomet data and return it as a pandas DataFrame.
"""

import json

import numpy as np
import pandas as pd
from osgeo import gdal
from scipy.stats import pearsonr
from sklearn import metrics

# We call gdal.UseExceptions() to raise exceptions instead of
# returning error codes like None. See here: https://gdal.org/api/python_gotchas.html
gdal.UseExceptions()
gdal.SetConfigOption("GTIFF_SRS_SOURCE", "EPSG")


def correct_invalid_rh(rh: np.ndarray) -> np.ndarray:
    """Apply sanity corrections to the RH predictions."""

    rh[rh > 100] = 100
    rh[rh < 0] = 0
    return rh


def create_geotiff(savepath: str, **kwargs):
    """Write a numpy array to a compressed Geotiff file."""

    arr = kwargs["array"]
    crs = kwargs["crs"]
    geoTF = kwargs["geoTF"]
    ndv = kwargs.get("ndv", -9999)

    driver = gdal.GetDriverByName("GTiff")

    gtiff = driver.Create(
        savepath,
        xsize=arr.shape[2],
        ysize=arr.shape[1],
        bands=arr.shape[0],
        eType=gdal.GDT_Float32,
        options=["COMPRESS=DEFLATE", "BIGTIFF=IF_NEEDED"],
    )
    gtiff.SetGeoTransform(geoTF)
    gtiff.SetProjection(crs)

    try:
        for i in range(arr.shape[0]):
            band = gtiff.GetRasterBand(i + 1)
            band.WriteArray(arr[i, ...].astype(np.float32))
            band.SetNoDataValue(ndv)
    except:
        raise ValueError("Failed to write data to GeoTiff.")

    gtiff.FlushCache()


def create_json(savepath: str, data: dict):
    """Write a dictionary to a JSON file."""

    with open(savepath, "w") as f:
        json.dump(data, f, sort_keys=True, indent=4, ensure_ascii=False)


def evaluate(true: np.ndarray, test: np.ndarray) -> dict:
    """Compare the true values with the test values."""

    r, pval = pearsonr(true, np.squeeze(test))

    scores = {
        "R2": metrics.r2_score(true, test),
        "r": r,
        "pval": pval,
        "MAE": metrics.mean_absolute_error(true, test),
        "MedAE": metrics.median_absolute_error(true, test),
        "MSE": metrics.mean_squared_error(true, test),
        "N": len(test),
    }
    return scores


def read_raster(fpath: str, ndv=-9999) -> dict:
    """Read the features from a Geotiff file."""

    ds = gdal.Open(str(fpath))

    arr = ds.ReadAsArray().astype(np.float32)
    arr[arr == ndv] = np.nan
    arr = np.ma.masked_invalid(arr)
    if ds.RasterCount == 1:
        arr = np.expand_dims(arr, axis=0)

    geoTF = ds.GetGeoTransform()
    crs = ds.GetProjection()
    width = ds.RasterXSize
    height = ds.RasterYSize

    ds = None

    MinX = geoTF[0]
    MinY = geoTF[3] + geoTF[5] * height
    MaxX = geoTF[0] + geoTF[1] * width
    MaxY = geoTF[3]

    data = {
        "array": arr,
        "coords_x": np.linspace(MinX, MaxX, width, endpoint=True),
        "coords_y": np.linspace(MaxY, MinY, height, endpoint=True),
        "geoTF": geoTF,
        "bounds": (MinX, MinY, MaxX, MaxY),
        "crs": crs,
        "N": arr.shape[0],
    }
    return data


def sample_raster(raster: np.ndarray, point: list) -> np.ndarray:
    """Sample the raster data at the given points."""

    col = np.argmin(np.abs(raster["coords_x"] - point.coord_x))
    row = np.argmin(np.abs(raster["coords_y"] - point.coord_y))
    return raster["array"][:, row, col]


def read_geojson(fpath: str, vars: list) -> pd.DataFrame:
    """Read a geojson file with biomet data."""

    data = []
    with open(fpath) as f:
        data_dict = json.load(f)["features"]

    for station in data_dict:
        d = {var: station["properties"][var] for var in vars}
        d["name"] = station["properties"]["name"]
        d["coord_x"], d["coord_y"] = station["geometry"]["coordinates"]
        data.append(d)
    return pd.DataFrame.from_dict(data)
