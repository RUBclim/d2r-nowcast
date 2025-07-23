# Generating Predictors for the Interpolation Module

This document outlines the steps required to generate the final raster file containing predictors for the interpolation module. The process starts with a GeoPackage (GPKG) file and involves rasterization, preprocessing, and stacking.

## Data

The input data required for this process is the `predictors_v1.1.5_L0.gpkg` file. This file contains the relevant attributes that need to be rasterized and processed.

The creation of this file begins with the generation of a 100 m x 100 m grid vector file in QGIS. The attributes, which form the predictors, are derived by sampling multiple raster layers using zonal statistics and raster algebra. For example, the vegetation percentage is calculated as the ratio of vegetated pixels, derived from Google EIE’s tree canopy mask, to the total number of pixels within each grid cell.

## Processing Steps

To generate the GeoTIFF file that serves as input for the interpolation module, follow these steps:

### 1. Rasterize Attributes
Rasterize the relevant attributes from the `predictors_v1.1.5_L0.gpkg` file. This step converts vector data into raster format, ensuring that each attribute is represented as a separate raster layer.

### 2. Preprocess Rasters
Preprocess the rasterized layers from step 1. The preprocessing includes:
- **Smoothing**: Apply a Gaussian filter to smooth the data and reduce noise.
- **Scaling**: Scale the data to ensure all layers are on a comparable scale.
- **Masking**: Apply a mask to exclude pixes outside of the Region of Interest.

### 3. Stack Rasters
Combine the preprocessed raster layers into a single multi-band GeoTIFF file. Optionally, you can:
- Add the x and y coordinates as additional predictors.
- Postprocess the data by applying Principal Component Analysis (PCA) to address multi-collinearity among predictors.

### 4. Output
The final output is a single GeoTIFF file containing all the predictors required for the interpolation module.

## Automation
The above steps can be automated using the provided scripts in this repository. Ensure that all dependencies are installed and configured before running the scripts.
