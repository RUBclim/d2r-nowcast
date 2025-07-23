"""
Main function for interpolating the station data using Kriging.
"""

import argparse
import logging
from pathlib import Path

import helpers as utils
import numpy as np
import pandas as pd
from krige import KrigeBiomet
from regress import RegressionModelling

# SETTINGS
# ========
N_FOLDS = 4  # Number of folds for cross-validation.
N_REALIZ = 0  # Number of realizations for conditional kriging. To skip, set to 0.
N_STATIONS = 50  # Minimum number of stations for interpolation.
R2_THRES = 0.50  # Minimum R2 score for regression.
RESCORR = False  # Whether to apply residual correction.
VARS = ["air_temperature", "relative_humidity"]  # The geoJSON variables to interpolate.


def _calc_scores(station_data: pd.DataFrame, pred: dict, var: str) -> dict:
    """Compare the measured and predicted data."""

    y_true = station_data[var].values

    y_test = []
    for _, obs in station_data.iterrows():
        y_test.append(utils.sample_raster(pred[var], obs))

    return utils.evaluate(y_true, np.array(y_test))


def interpolate_biomet(
    savedir: str,
    savename_ta: str,
    savename_rh: str,
    fpath_biomet: str,
    fpath_features: str,
    ndv: int = -32768,
    save_interm: bool = True,
    verbosity=0,
) -> dict:
    """
    Interpolate station data and save the results as GeoTIFF.

    Workflow Paths:
    - 1.0: Regression (primary option).
    - 1.5: Regression Kriging (primary option).
    - 2.0: Universal Kriging (backup option if the first two fail).

    Parameters:
    - savedir (str): The dir where the output files will be stored.
    - savename_ta (str): The filename of the output TA GeoTIFF.
    - savename_rh (str): The filename of the output RH GeoTIFF.
    - fpath_biomet (str): The filepath of the biomet data in GeoJSON format.
    - fpath_features (str): The filepath of the features in GeoTIFF format.
    - ndv (int, optional): The NoDataValue for the features. Defaults to -32768.
    - save_interm (bool, optional): Whether to save intermediate results. Defaults to True.
    - verbosity (int, optional): The verbosity level for logging. Defaults to 0.

    Returns:
    - list(dict, float): A dict with the interpolated arrays and the path employed as a float.
    """

    if len(VARS) == 2:
        vars = VARS
        fnames_out = {vars[0]: savename_ta, vars[1]: savename_rh}
    else:
        raise SystemExit("VARS should include Tair and RH only!")

    match verbosity:
        case 0:
            verbosity_lvl = logging.WARNING
        case 1:
            verbosity_lvl = logging.INFO
        case 2:
            verbosity_lvl = logging.DEBUG
        case _:
            verbosity_lvl = logging.WARNING

    logging.basicConfig(level=verbosity_lvl)

    savedir = Path(savedir)
    if save_interm:
        (savedir / "intermediate").mkdir(
            parents=True, exist_ok=True
        )  # relevant only for wpaths 1.0 and 1.5.
    else:
        savedir.mkdir(parents=True, exist_ok=True)

    data = utils.read_geojson(fpath_biomet, vars)
    if len(data) < N_STATIONS:
        raise SystemExit(f"Not enough stations for interpolation.")

    features = utils.read_raster(fpath_features, ndv=ndv)
    nanmask = features["array"].mask.any(axis=0)[np.newaxis, ...]

    target_georef = {
        "coords_x": features["coords_x"],
        "coords_y": features["coords_y"],
        "geoTF": features["geoTF"],
        "crs": features["crs"],
    }

    X = {}
    for idx, point in data[["coord_x", "coord_y"]].iterrows():
        X[idx] = utils.sample_raster(features, point)

    feature_names = [f"x_{i}" for i in range(features["N"])]
    X = pd.DataFrame.from_dict(X, orient="index", columns=feature_names)

    data = data.join(X, how="left", validate="1:1")
    station_coords = (data["coord_x"].values, data["coord_y"].values)

    output = {}
    output_meta = {}

    rm = RegressionModelling()
    rm.n_splits = N_FOLDS
    models = {}
    scores_tr = []
    tuning_results = {}

    for var in vars:
        logging.info(f"Training regression model for {var}.")

        y = data[var]
        X = data[feature_names].values

        reg = rm.train_model(X, y)
        r2_cv = reg.best_score_
        r2_tr = reg.score(X, y)
        scores_tr.append(r2_tr)

        models[var] = {"reg": reg}
        tuning_results[var] = {
            "alpha": reg.alpha_,
            "r2_cv": reg.best_score_,
            "r2_tr": reg.score(X, y),
        }

        logging.info(f"R2_{var} scores: tr={r2_tr:0.2f}, cv={r2_cv:0.2f}.")

    if save_interm:
        savefile = savedir / "intermediate" / "regr_tuning.json"
        utils.create_json(savefile, tuning_results)

    if max(scores_tr) >= R2_THRES:

        if RESCORR == True:
            wpath = 1.5
        else:
            wpath = 1.0

        resids = {}

        for var in vars:
            logging.info(
                f"Applying regression model for {var} (worfklow path: {wpath})."
            )

            reg = models[var]["reg"]
            y_hat = rm.apply_model(reg, features["array"])

            if var == "relative_humidity":
                y_hat = utils.correct_invalid_rh(y_hat)

            y_hat = {
                "array": y_hat,
                "N": 1,
                "ndv": np.nan,
                **target_georef,
            }

            if save_interm:
                savefile = str(savedir / "intermediate" / f"{var}_regr.tif")
                utils.create_geotiff(savefile, **y_hat)

            resids[var] = []
            for _, obs in data.iterrows():
                resid = obs[var] - utils.sample_raster(y_hat, obs)[0]
                resids[var].append(resid)

            output[var] = y_hat

        if save_interm:
            savefile = savedir / "intermediate" / "regr_residuals.json"
            utils.create_json(savefile, resids)

    else:
        wpath = 2.0

    logging.info(f"Applying kriging (worfklow path: {wpath}).")

    match wpath:
        case 1.0:
            scores = {}
            for var in vars:
                savefile = str(savedir / fnames_out[var])
                utils.create_geotiff(savefile, **output[var])
                scores[var] = _calc_scores(data, output, var)

            output_meta["qc"] = int(
                max([scores[var]["R2"] for var in vars]) >= R2_THRES
            )
            output_meta["wpath"] = wpath
            output_meta["scores"] = scores
            utils.create_json(savedir / "output_meta.json", output_meta)
            return output, output_meta

        case 1.5:
            data_to_krige = {var: np.array(resids[var]) for var in vars}

        case 2.0:
            data_to_krige = {var: data[var].values for var in vars}

        case _:
            raise SystemExit("Invalid worfklow path.")

    uk = KrigeBiomet(
        coords=station_coords,
        ta=data_to_krige[vars[0]],
        rh=data_to_krige[vars[1]],
    )

    uk.fit_variogram()
    if len(uk.covmodels) == len(vars):

        kriged = {}

        interpolated_arrays = uk.interpolate(
            features["coords_x"],
            features["coords_y"],
            n_realizations=N_REALIZ,
        )

        # Make sure the dict keys agree with the used variable names
        # and the arrays are masked where the features are masked.
        for i, arr in enumerate(interpolated_arrays.values()):
            arr[nanmask] = np.nan
            kriged[vars[i]] = {"array": arr, "N": 1, "ndv": np.nan, **target_georef}

        for var in vars:

            if wpath == 1.5:
                output[var]["array"] += kriged[var]["array"]
            else:
                output[var] = kriged[var]

            if var == "relative_humidity":
                output[var]["array"] = utils.correct_invalid_rh(output[var]["array"])

            if save_interm and wpath < 2.0:
                savefile = str(savedir / "intermediate" / f"{var}-resids_kriged.tif")
                utils.create_geotiff(savefile, **kriged[var])

            # Create the final GeoTIFFs.
            savefile = str(savedir / fnames_out[var])
            utils.create_geotiff(savefile, **output[var])

    else:
        logging.critical(f"Covmodel fit failed (worfklow path: {wpath}).")

    if len(output) == 0:
        raise SystemExit("Output is empty. No GeoTIFFs where created.")  # Crash?

    scores = {}
    for var in vars:
        scores[var] = _calc_scores(data, output, var)

    output_meta["qc"] = int(max([scores[var]["R2"] for var in vars]) >= R2_THRES)
    output_meta["wpath"] = wpath
    output_meta["scores"] = scores
    utils.create_json(savedir / "output_meta.json", output_meta)

    logging.info(f"{Path(fpath_biomet).name} has been processed succesfully.")

    return output, output_meta


def cli():
    """Command-line interface."""

    parser = argparse.ArgumentParser(
        description="Interpolate the station data using regression kriging"
    )
    parser.add_argument(
        "savedir",
        type=str,
        help="The dir where the output files will be stored.",
    )
    parser.add_argument(
        "savename_ta",
        type=str,
        help="The filename of the output TA GeoTIFF.",
    )
    parser.add_argument(
        "savename_rh",
        type=str,
        help="The filename of the output RH GeoTIFF.",
    )
    parser.add_argument(
        "fpath_biomet",
        type=str,
        help="The filepath of the biomet data.",
    )
    parser.add_argument(
        "fpath_features",
        type=str,
        help="The filepath of the features.",
    )
    parser.add_argument(
        "--ndv",
        type=str,
        default=-32768,
        help="The NoData value of the features.",
    )
    parser.add_argument(
        "--save_interm",
        type=bool,
        default=True,
        help="Whether to save intermediate results.",
    )
    parser.add_argument(
        "--verbose",
        type=int,
        default=0,
        help="The verbosity level.",
    )

    args = parser.parse_args()

    interpolate_biomet(
        args.savedir,
        args.savename_ta,
        args.savename_rh,
        args.fpath_biomet,
        args.fpath_features,
        args.ndv,
        args.verbose,
    )


if __name__ == "__main__":
    cli()
