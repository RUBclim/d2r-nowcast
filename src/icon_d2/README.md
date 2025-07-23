# d2r-icon2d

Download the most recent ICON-D2 forecasts for Dortmund and calculate various thermal comfort indices.

## ICON-D2

ICON is the global and regional numerical weather prediction model at DWD. Forecasts of ICON-D2 are performed 8 times a day (namely at 00, 03, 06, 09, 12, 15, 18, 21 UTC), with a forecast range of 48 h, and are distributed as `grib2` files via [opendata.dwd.de](https://opendata.dwd.de/weather/nwp/icon-d2/grib/). More information about ICON-D2 can be found [here](https://www.dwd.de/DWD/forschung/nwv/fepub/icon_database_main.pdf).

## Workflow

### `download_nwp()`

For each field (i.e., `t_2m`), `download_nwp()` will download the latest Numerical Weather Prediction (NWP) for ICON-D2 using DWD's [`downloader`](https://github.com/DeutscherWetterdienst/downloader). It will then use [`cdo`](https://code.mpimet.mpg.de/projects/cdo) to merge the files into a single netCDF4 file containing only the data over Dortmund. The output files will be stored within the `./data` directory, while the initial grib2 data will be temporarily stored in a separate folder and deleted once the processing is concluded.

### `calc_indices()`

The function `calc_indices()` will use the NWP as input to calculate various thermal comfort indices.

## Usage

1. Set the following parameters in `main.py`:
    - `model`: ICON grid model
    - `grid`: ICON grid type
    - `fields`: output fields
    - `lonW`, `lonE`, `latS`, `latN`: bounding box coordinates in degrees
    - `start`, `end`, `step`: forecast range in hours
    - `savedir`: save directory
2. Run the script in your terminal or IDE

### Output

The script saves the downloaded files in the specified `savedir` directory.

## Requirement

For `download_nwp.py` to run, it requires to have the following [module](https://github.com/DeutscherWetterdienst/downloader) installed. After cloning the repo, install it like this:

```python
pip install --editable .
```
