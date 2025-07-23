# Acknowledgment

## Data Source

The used netCDF file `nwp-20240821-06-relhum.nc` for testing the alignment of rasters, located in the same directory as this note, has the following source: **Deutscher Wetterdienst (DWD)**

The DWD ICON-D2 NWP model generated the example file, which shows the relative humidity 2 meters above the ground in Dortmund on August 21, 2024. This file is part of the ICON-D2 model's output from August 21, 2024, at 06:00 UTC.

> More details about the ICON-D2 model can be found [here](https://dwd-geoportal.de/products/G_E6D/), while a recent product of the relhum_2m model data can be obtained from [here](https://opendata.dwd.de/weather/nwp/icon-d2/grib/06/relhum_2m/).


The source of the NWP data has also been added to the file global attributes, as evident below:

```
import xarrax as xr
ds=xr.open_dataset('src/tests/test_data/align_rasters_test_data/nwp-20240821-06-relhum_2m.nc')
ds

<xarray.Dataset>
Dimensions:  (time: 49, lon: 80, lat: 51, height: 1)
Coordinates:
  * time     (time) datetime64[ns] 2024-08-21T06:00:00 ... 2024-08-23T06:00:00
  * lon      (lon) float64 6.2 6.22 6.24 6.26 6.28 ... 7.7 7.72 7.74 7.76 7.78
  * lat      (lat) float64 50.7 50.72 50.74 50.76 ... 51.64 51.66 51.68 51.7
  * height   (height) float64 2.0
Data variables:
    2r       (time, height, lat, lon) float32 ...
Attributes:
    CDI:          Climate Data Interface version 2.1.1 (https://mpimet.mpg.de...
    Conventions:  CF-1.6
    institution:  Deutscher Wetterdienst
    history:      Wed Aug 21 12:00:37 2024: cdo -f nc -seltime,00:00,01:00,02...
    CDO:          Climate Data Operators version 2.1.1 (https://mpimet.mpg.de...
```

As of the day of adding this file and the corresponding netCDF to the repository, the legal notice of DWD allows using their data with the following claim

> "All open spatial data and spatial data services of the DWD as well as all DWD services that are defined as high-value datasets (HVD) may be re-used under the Creative Commons licence conditions CC BY 4.0 provided that the source is acknowledged. Spatial data here includes any location-related weather and climate information offered for access."
>
> Source: https://www.dwd.de/EN/service/legal_notice/legal_notice_node.html
