"""
A class to interpolate the biomet data using universal kriging.
"""

import logging

import gstools as gs
import numpy as np


class KrigeBiomet:
    """
    A class to interpolate the biomet's TA and RH data using universal kriging.

    Methods:
    --------
    __init__(coords: tuple, ta: np.ndarray, rh: np.ndarray, n_bins=16, max_dist=10000):
        Initializes the InterpolateBiomet class with coordinates, temperature, and RH data.

    _estimate_empirical_variograms() -> tuple[np.ndarray, np.ndarray]:
        Estimates the empirical variogram for each variable.

    fit_variogram() -> tuple:
        Fits the variogram model to an empirical variogram.

    interpolate(x_dst: np.ndarray, y_dst: np.ndarray, conditioned=False) -> dict[np.ndarray, np.ndarray]:
        Uses universal kriging to interpolate the temperature and RH data.
    """

    n_dims = 2
    _exact = True

    @property
    def exact(self):
        """Whether the interpolator is exact."""
        return type(self)._exact

    @exact.setter
    def exact(self, val):
        if not isinstance(val, bool):
            raise TypeError("exact should be a boolean.")
        type(self)._exact = val

    def __init__(
        self, coords: tuple, ta: np.ndarray, rh: np.ndarray, n_bins=16, max_dist=5000
    ):
        """
        Initialize the InterpolateBiomet class.

        Parameters:
        -----------
        coords : tuple
            Tuple containing arrays of the x and y coordinates (in meters).3
        ta : np.ndarray
            Array of temperature data.
        rh : np.ndarray
            Array of relative humidity data.
        n_bins : int, optional
            Number of bins for the variogram (default is 16).
        max_dist : int, optional
            Maximum distance for the variogram (default is 10000 m).

        Raises:
        -------
        SystemExit
            If the sizes of ta, rh, and coords do not match.
        """

        if ta.size == rh.size == coords[0].size:
            self.data = {"ta": ta, "rh": rh}
            self.coords_in = coords
        else:
            raise SystemExit("ta, rh and coords must have the same length.")

        self.bins = gs.variogram.standard_bins(
            coords,
            dim=self.n_dims,
            bin_no=n_bins,
            max_dist=max_dist,
        )

    def _estimate_empirical_variograms(self) -> tuple[np.ndarray, np.ndarray]:
        """Estimate the empirical directional variogram for each variable."""

        empirical_variogram = {}

        args = {
            "bin_edges": self.bins,
            "return_counts": False,
        }

        for var, data in self.data.items():
            bin_centers, gamma = gs.vario_estimate(self.coords_in, data, **args)
            empirical_variogram[var] = gamma

        return bin_centers, empirical_variogram

    def fit_variogram(self) -> tuple:
        """Fits an exp variogram model to an empirical variogram."""

        bin_centers, variograms = self._estimate_empirical_variograms()

        self.covmodels = {}

        for var, gamma in variograms.items():

            model = gs.Exponential(dim=self.n_dims)

            try:
                _, _, r2 = model.fit_variogram(
                    bin_centers,
                    gamma,
                    nugget=True,
                    return_r2=True,  # pseudo R2
                )
            except RuntimeError:
                return {}
            else:
                logging.info(f"Variogram fit R2_{var} = {r2:0.2f}.")
                self.covmodels[var] = {"model": model, "r2": r2}

        return self.covmodels

    def interpolate(
        self, x_dst: np.ndarray, y_dst: np.ndarray, n_realizations=0
    ) -> dict[np.ndarray, np.ndarray]:
        """
        Use universal kriging to interpolate the ta and rh fields.

        Parameters:
        -----------
        x_dst : np.ndarray
            Array of x-coordinates for the destination grid.
        y_dst : np.ndarray
            Array of y-coordinates for the destination grid.
        n_realizations : int, optional
            Number of realizations for conditional simulation (default is 0, i.e. no simulation).

        Returns:
        --------
        dict[np.ndarray, np.ndarray]
            A dictionary containing the interpolated arrays
        """

        interpolated_data = {}

        for var, covmodel in self.covmodels.items():

            krig = gs.krige.Universal(
                model=covmodel["model"],
                cond_pos=self.coords_in,
                cond_val=self.data[var],
                drift_functions="linear",
                exact=self.exact,
            )

            # Set positions and mesh_type:
            krig.set_pos((x_dst, y_dst), mesh_type="structured")

            # Generate the kriging field.
            krig(return_var=False, store=f"field_{var}")

            if n_realizations > 0:

                cond_srf = gs.CondSRF(krig)
                cond_srf.set_pos([x_dst, y_dst], "structured")

                seed = gs.random.MasterRNG(323582)
                for i in range(n_realizations):
                    cond_srf(seed=seed(), store=[f"fld{i}", False, False])

                realizations = [cond_srf[f"fld{i}"] for i in range(n_realizations)]
                interpolated_data[var] = np.mean(realizations, axis=0).T[
                    np.newaxis, ...
                ]

            else:
                interpolated_data[var] = krig[f"field_{var}"].T[np.newaxis, ...]

        return interpolated_data
