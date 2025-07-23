"""
This script tests the raster aligning tool.

Functions:
- get_lonlat: Returns lon/lat coordinates from a GeoTIFF raster.
- get_bbox_coords: Returns bbox coordinates form a GeoTIFF raster.
- test_align_rasters: Tests that the aligned raster has the expected properties.
"""

import os

import numpy as np
import osgeo
from affine import Affine
from osgeo import gdal, osr

from src.utils.align_rasters import RasterAligner

from .test_utils import clear_tmp_dir, create_dummy_raster

gdal.UseExceptions()

def get_lonlat(raster) -> tuple:
    """
    Get Lon Lat from raster center as a tuple: lat at [0], lon at [1]
    Conversion from UMEP Toolbox
    https://github.com/UMEP-dev/UMEP-processing/blob/b7e6c441e1fd115b8c83ee164cf1bcb3a7a794b3/processor/solweig_algorithm.py#L415C1-L441C54
    """
    proj = raster.GetProjection()
    srs = osr.SpatialReference(wkt=proj)

    if int(osgeo.__version__[0]) >= 3:
        # GDAL 3 changes axis order: https://github.com/OSGeo/gdal/issues/1546
        srs.SetAxisMappingStrategy(osgeo.osr.OAMS_TRADITIONAL_GIS_ORDER)

    # Get latlon from grid coordinate system
    old_cs = osr.SpatialReference()
    old_cs.ImportFromWkt(proj)

    wgs84_wkt = """
    GEOGCS["WGS 84",
        DATUM["WGS_1984",
            SPHEROID["WGS 84",6378137,298.257223563,
                AUTHORITY["EPSG","7030"]],
            AUTHORITY["EPSG","6326"]],
        PRIMEM["Greenwich",0,
            AUTHORITY["EPSG","8901"]],
        UNIT["degree",0.01745329251994328,
            AUTHORITY["EPSG","9122"]],
        AUTHORITY["EPSG","4326"]]"""

    new_cs = osr.SpatialReference()
    new_cs.ImportFromWkt(wgs84_wkt)

    transform = osr.CoordinateTransformation(old_cs, new_cs)
    width = raster.RasterXSize
    height = raster.RasterYSize

    geotransform = raster.GetGeoTransform()

    # transform center coords rather than ul/ur coords
    affine_transform = Affine.from_gdal(*geotransform)
    centerx, centery = affine_transform * (0.5 * width, 0.5 * height)  # center

    return transform.TransformPoint(centerx, centery)


def get_bbox_coords(ds: gdal.Dataset) -> tuple:
    """Get te upper left and lower right bounding box coordinates"""
    ulx, xres, _, uly, _, yres = ds.GetGeoTransform()
    lrx = ulx + (ds.RasterXSize * xres)
    lry = uly + (ds.RasterYSize * yres)
    return (ulx, lry, lrx, uly)


def test_align_rasters():
    """
    Tests align_rasters.py tool by checking the shape, CRS, lon/lat and bounding box coords.
    """

    data_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "test_data",
        "align_rasters_test_data",
    )
    save_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tmp")
    clear_tmp_dir(save_dir)

    create_dummy_raster(save_dir, "dummy_raster.tif")

    fpath_ref = os.path.join(save_dir, "dummy_raster.tif")
    ref_epsg = 25832
    src_epsg = 4326
    ndv = -32768
    method = "cubic"
    savefile = os.path.join(save_dir, "aligned_raster.tif")
    fpath_src = os.path.join(data_dir, "nwp-20240821-06-relhum_2m.nc")
    band = 3

    aligner = RasterAligner(fpath_ref, ref_epsg)
    aligner.set_warp_options(src_epsg, ndv, method)
    aligner.warp_raster(savefile, fpath_src, band)

    ref = gdal.Open(fpath_ref)
    ref_arr = np.array(ref.GetRasterBand(1).ReadAsArray())
    gen = gdal.Open(savefile)
    gen_arr = np.array(gen.GetRasterBand(1).ReadAsArray())

    assert (
        gen_arr.shape == ref_arr.shape
    ), "Aligned raster should have the same shape as the reference raster."

    proj = gen.GetProjection()
    srs = osr.SpatialReference(wkt=proj)
    gen_epsg = srs.GetAttrValue("Authority", 1)
    assert gen_epsg == str(
        ref_epsg
    ), "Aligned raster should have the same CRS as the reference raster."

    assert get_lonlat(gen) == get_lonlat(
        ref
    ), "Aligned raster should have the same longitude/latitude location as the reference raster."

    assert get_bbox_coords(gen) == get_bbox_coords(
        ref
    ), "The bounding box coordinates of the aligned raster and the reference raster should match."
