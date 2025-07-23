# -*- coding: utf-8 -*-
"""
Warp the source raster to a reference raster and store the result as a new file.
"""

import argparse
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from osgeo import gdal, osr

# We call gdal.UseExceptions() to raise exceptions instead of
# returning error codes like None. See here: https://gdal.org/api/python_gotchas.html
gdal.UseExceptions()


@dataclass
class RasterAligner:
    """Warp a Raster to another raster."""

    dst_fpath: str
    dst_epsg: int = None
    warp_options: gdal.WarpOptions = None

    def __post_init__(self):
        """Use the reference raster to initialize the RasterAligner object."""

        dst = gdal.Open(str(self.dst_fpath))

        if self.dst_epsg is not None:
            srs = self._get_srs_from_epsg(self.dst_epsg)
        else:
            proj = dst.GetProjection()
            if len(proj) > 0:
                srs = osr.SpatialReference(wkt=proj)
            else:
                raise ValueError("Cannot determine the file's SRS. Provide EPSG code.")

        self.dst_srs = srs
        self.dst_width = dst.RasterXSize
        self.dst_height = dst.RasterYSize
        self.dst_bounds = self._get_bbox_coords(dst)
        dst = None

    def _get_bbox_coords(self, ds: gdal.Dataset) -> tuple:
        """Get te upper left and lower right bounding box coordinates"""
        ulx, xres, _, uly, _, yres = ds.GetGeoTransform()
        lrx = ulx + (ds.RasterXSize * xres)
        lry = uly + (ds.RasterYSize * yres)
        return (ulx, lry, lrx, uly)

    def _get_srs_from_epsg(self, epsg: int) -> osr.SpatialReference:
        """Get an OpenGIS SRS representation for the given EPSG code."""
        srs = osr.SpatialReference()
        srs.ImportFromEPSG(epsg)
        return srs

    def set_warp_options(
        self, src_epsg: int, ndv: float, method="cubic", file_format="GTiff"
    ) -> gdal.WarpOptions:
        """Use the reference raster to set the Warp options.

        Args:
            src_epsg (int): The src's EPSG code (for the ICON-D2 data use 4326).
            ndv (float): The src NoData value.
            method (str, optional): The resampling method. Defaults to "cubic".
            file_format (str, optional): The output format. Defaults to "GTiff".
        """

        methods = {
            "average": gdal.GRA_Average,
            "nearest": gdal.GRA_NearestNeighbour,
            "majority": gdal.GRA_Mode,
            "cubic": gdal.GRA_Cubic,
            "bilinear": gdal.GRA_Bilinear,
            "lanczos": gdal.GRA_Lanczos,
            "cubicspline": gdal.GRA_CubicSpline,
        }

        if method not in methods:
            raise KeyError(
                f"Invalid resampling method. Choose one of: {', '.join(methods.keys())}."
            )

        # For explanations see: https://gdal.org/api/python/osgeo.gdal.html#osgeo.gdal.WarpOptions
        self.warp_options = gdal.WarpOptions(
            outputBounds=self.dst_bounds,
            outputBoundsSRS=self.dst_srs,
            srcSRS=self._get_srs_from_epsg(src_epsg),
            dstSRS=self.dst_srs,
            width=self.dst_width,
            height=self.dst_height,
            srcNodata=ndv,
            dstNodata=ndv,
            resampleAlg=methods[method],
            format=file_format,
        )

        return self.warp_options

    def warp_raster(
        self, fpath_out: str, fpath_in: str, band: int, return_as_array=False
    ) -> np.ndarray | None:
        """Warp the source raster to a reference raster and store the result as a new file."""

        if not isinstance(band, int):
            raise TypeError("The band argument must be an integer.")

        if self.warp_options is not None:
            # Because we use GDAL v.3.6.x, we cannot pass the band argument in gdal.WarpOption.
            # To work around this we first use gdal.Translate() to create a VRT file with the
            # desired band and then warp the VRT file.
            fpath_in = Path(fpath_in)
            fpath_vrt = fpath_in.parent / f"{fpath_in.name}_b{band}.vrt"
            gdal.Translate(str(fpath_vrt), str(fpath_in), format="VRT", bandList=[band])
            gdal.Warp(fpath_out, str(fpath_vrt), options=self.warp_options)
            fpath_vrt.unlink()  # remove the temporary VRT file

        else:
            raise ValueError(
                "Warp options are not set. Use the set_warp_options method first."
            )

        if return_as_array:
            return gdal.Open(fpath_out).ReadAsArray()
        return None


def cli() -> None:
    """Command-line interface."""

    parser = argparse.ArgumentParser(
        description="Align the source raster to a reference raster using GDAL's warp."
    )

    parser.add_argument(
        "fpath_src",
        type=str,
        help="the source raster filepath.",
    )
    parser.add_argument(
        "fpath_ref",
        type=str,
        help="the reference raster filepath.",
    )
    parser.add_argument(
        "band",
        type=int,
        help="The src band that will be warped.",
    )
    parser.add_argument(
        "savefile",
        type=str,
        help="The warped raster savefile.",
    )
    parser.add_argument(
        "--ndv",
        type=float,
        default=-32768,
        help="the src NoData value.",
    )
    parser.add_argument(
        "--src_epsg",
        type=int,
        default=4326,
        help="The src's EPSG code.",
    )
    parser.add_argument(
        "--ref_epsg",
        type=int,
        default=25832,
        help="The ref's EPSG code.",
    )
    parser.add_argument(
        "--method",
        type=str,
        default="cubic",
        help="the resampling method",
    )

    args = parser.parse_args()

    aligner = RasterAligner(args.fpath_ref, args.ref_epsg)
    aligner.set_warp_options(args.src_epsg, args.ndv, args.method)
    aligner.warp_raster(args.savefile, args.fpath_src, args.band)


if __name__ == "__main__":
    cli()
