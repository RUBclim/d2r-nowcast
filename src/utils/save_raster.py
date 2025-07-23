"""
Script to save a data array as geotiff based on a reference raster.
"""

import argparse

from osgeo import gdal

gdal.UseExceptions()


def saveraster(reference_raster, output_location, data_array):
    """
    Saves a data_array as geotiff with georeference from the given
    reference_raster at given output_location with lossless LZW compression

    Args:
        reference_raster (gdal Dataset): opened geotiff dataset
        output_location (str) : output file location
        data_array (numpy array): raster data
    """
    driver = gdal.GetDriverByName("GTiff")
    size1, size2 = data_array.shape
    dataset_output = driver.Create(
        output_location,
        xsize=size2,
        ysize=size1,
        bands=1,
        eType=gdal.GDT_Float32,
        options=["COMPRESS=LZW"],
    )
    dataset_output.SetGeoTransform(reference_raster.GetGeoTransform())
    dataset_output.SetProjection(reference_raster.GetProjection())
    dataset_output.GetRasterBand(1).WriteArray(data_array)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--array", help="2D numpy array to save")
    parser.add_argument("-r", "--reference", help="GeoTIFF with reference projection")
    parser.add_argument("-o", "-output", help="Output location")
