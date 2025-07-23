# 🌡️ Data2Resilience Nowcasting Service Backend

This repository powers the backend of Data2Resilience (D2R)'s nowcasting service, which monitors urban heat and outdoor thermal discomfort in Dortmund, Germany.

D2R models the [Universal Thermal Comfort Index (UTCI)](https://utci.org/index.html) at street-level resolution every one hour, using as a basis data from [D2R's biometeorological weather station network](https://dashboard.data2resilience.de/en/stations) and numerical weather predictions (NWP) from the German Weather Service (DWD). At its core, the nowcasting service uses the SOLWEIG model from the [Urban Multi-scale Environmental Predictor (UMEP)](https://umep-docs.readthedocs.io/en/latest/).

The output data are visualized in the Data2Resilience [dashboard](https://dashboard.data2resilience.de/) (not part of this repository).

## Structure

This repository is structured as follows:

- `docs/` - Project documentation. See the [README](./docs/README.md) for more details.

- `src/` - Main processing scripts and pipeline setup.
  - `src/icon_d2/` - Downloads and prepares the ICON-D2 NWP from DWD.
  - `src/interpolate/` - Processes the weather station data into continuous city-wide rasters.
  - `src/umep_wrapper/` - Contains scripts that call or relate to the `UMEP-toolbox`.
  - `src/umep_wrapper/config-templates/`: Configuration templates for running the UMEP's Wall, SVF, and SOLWEIG modules.

- `tests/`: Functional tests. See Run Tests section below for usage.

## Setup and Usage

The backend functionality is delivered through a docker image that has to be build and run as a prediodic [`cron`](https://en.wikipedia.org/wiki/Cron) job. For step-by-step installation instructions, refer to the dedicated guide in the  [documentation](docs/source/documentation/06_install_and_use.rst).

### External Dependencies

The following external projects must be installed alongside `d2r-nowcast`:

- [`DWD-downloader`](https://github.com/DeutscherWetterdienst/downloader) — used to retrieve GRIB2-format NWP data from the DWD file server (version 0.2.0)
- [`UMEP-processing-fork`](https://github.com/luise-wei/UMEP-processing-fork/tree/standalone-solweig) — enables standalone execution of thermal comfort algorithms within the UMEP toolbox


## Run Tests

This repository includes unittests for the core pipeline components. To run the tests in a virtual environment:

```bash
(venv) pytest -v -s
```

- `-v` enables verbose output
- `-s` displays `stdout` during test execution

If you are using a conda environment you need to export the `PROJ_LIB` parameter:

```bash
export PROJ_LIB=/path/to/conda/envs/venv-name/share/proj/
```

Make sure to also install the [`UMEP-processing-fork`](https://github.com/luise-wei/UMEP-processing-fork/tree/standalone-solweig):

```bash
(venv) ~/../path/to/UMEP-processing-fork$ pip install -e .
```


## Project Funding

This project was funded by [ICLEI Europe](https://iclei-europe.org/) through the [ICLEI Action Fund 2.0](https://iclei-europe.org/funding-opportunities/action-fund), a granting scheme supported by [Google.org](https://www.google.org/), under the project "Data2Resillience: Data-driven
Urban Climate Adaptation".
