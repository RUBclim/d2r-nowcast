"""Script to convert temperatures in a raster from Kelvin to Celsius."""

import argparse

import numpy as np
from osgeo import gdal

gdal.UseExceptions()


def convert_geotiff(input_path, output_path):
    """Read a GeoTIFF file, convert temperatures from Kelvin to Celsius, and save the result."""
    # Open the input GeoTIFF file
    dataset = gdal.Open(input_path)
    band = dataset.GetRasterBand(1)

    # Read the data as a numpy array
    kelvin_data = band.ReadAsArray()

    # Convert the data from Kelvin to Celsius
    celsius_data = kelvin_data - 273.15

    # Get the geotransform and projection from the input dataset
    geotransform = dataset.GetGeoTransform()
    projection = dataset.GetProjection()

    # Create the output GeoTIFF file
    driver = gdal.GetDriverByName("GTiff")
    out_dataset = driver.Create(
        output_path, dataset.RasterXSize, dataset.RasterYSize, 1, gdal.GDT_Float32
    )

    # Set the geotransform and projection on the output dataset
    out_dataset.SetGeoTransform(geotransform)
    out_dataset.SetProjection(projection)

    # Write the data to the output dataset
    out_band = out_dataset.GetRasterBand(1)
    out_band.WriteArray(celsius_data)

    # Flush data to disk
    out_band.FlushCache()

    # Close the datasets
    dataset = None
    out_dataset = None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Convert GeoTIFF from Kelvin to Celsius."
    )
    parser.add_argument(
        "-i", "--input_path", type=str, help="Path to the input GeoTIFF file."
    )
    parser.add_argument(
        "-o", "--output_path", type=str, help="Path to the output GeoTIFF file."
    )

    args = parser.parse_args()
    convert_geotiff(args.input_path, args.output_path)
