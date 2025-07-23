#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Smooth, rescale, and mask each predictor.
"""

from pathlib import Path

import numpy as np
import rasterio as rio
from astropy.convolution import convolve
from scipy import signal
from sklearn.preprocessing import RobustScaler

QMIN = 1
QMAX = 95
FILL_VALUE = -32768
KERNEL_SIZE = 9
KERNEL_SIGMA = 1.3
ITERS = 2


def gaussian_kernel(n, std, normalised=False):
    """
    Generates a n x n matrix with a centered gaussian
    of standard deviation std centered on it. If normalised,
    its volume equals 1.
    """
    gaussian1D = signal.windows.gaussian(n, std)
    gaussian2D = np.outer(gaussian1D, gaussian1D)
    if normalised:
        gaussian2D /= 2 * np.pi * (std**2)
    return gaussian2D


def apply_mask(array, mask):
    """Mask an array"""
    mask = np.broadcast_to(mask, array.shape)
    array[np.isnan(array)] = FILL_VALUE
    array[mask != 1] = FILL_VALUE
    return np.ma.masked_equal(array, FILL_VALUE)


def read_raster(fpath):
    """Read and clip a raster to the study area bounds"""
    with rio.open(fpath) as ds:
        data = ds.read()
        tf = ds.transform
        crs = ds.crs
    return data.astype(np.float32), tf, crs


def robust_scaler(array):
    """Rescale array to [-1, 1] using the QMIN and QMAX quantiles"""
    bands, height, width = array.shape

    mask = array.mask
    out = np.empty(shape=(bands, height, width), dtype=np.float32)

    for i, arr in enumerate(array):
        tf = RobustScaler(quantile_range=(QMIN, QMAX))
        tf.fit(arr.compressed().reshape(-1, 1))
        out[i, :, :] = tf.transform(arr.reshape(-1, 1)).reshape(1, height, width)

    out[mask] = FILL_VALUE
    return np.ma.masked_equal(out, FILL_VALUE)


def main(apply_filter=True):
    workdir = Path.cwd()

    print("Creating tiff with predictors... ", end="")

    citymask, tf, crs = read_raster("./citymask_100m.tif")

    savepath = workdir / "L1"
    savepath.mkdir(parents=True, exist_ok=True)

    datadir_L0 = workdir / "L0"

    for fpath in datadir_L0.glob("*.tif"):
        L0, _, _ = read_raster(fpath)
        L0 = apply_mask(L0, citymask)
        _, height, width = L0.shape

        L0[L0 == FILL_VALUE] = np.nan

        if apply_filter:
            kernel = gaussian_kernel(KERNEL_SIZE, KERNEL_SIGMA)

            n_iterations = 0
            while n_iterations < ITERS:
                L0 = convolve(
                    np.squeeze(L0),
                    kernel,
                    boundary="extend",
                    normalize_kernel=True,
                    preserve_nan=True,
                )
                n_iterations += 1

            L0[np.isnan(L0)] = FILL_VALUE
            L0 = L0[np.newaxis, :, :]

        L1 = robust_scaler(apply_mask(L0, citymask))
        L1 = apply_mask(L1, citymask)

        gtiff_profile = rio.profiles.DefaultGTiffProfile(
            count=L1.shape[0],
            height=height,
            width=width,
            dtype=str(L1.dtype),
            crs=crs,
            nodata=FILL_VALUE,
            transform=tf,
        )

        with rio.open(
            savepath / f"{fpath.stem}_L1.tif",
            "w",
            **gtiff_profile,
        ) as dst:
            dst.write(L1)

    print("Done")


if __name__ == "__main__":
    main()
