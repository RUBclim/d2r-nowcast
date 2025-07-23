# -*- coding: utf-8 -*-
"""
A multi-output regression model.
"""

import numpy as np
from sklearn.linear_model import RidgeCV


class RegressionModelling:
    """A multi-output regression model."""

    SEED = 2612136

    _n_splits = 4

    @property
    def n_splits(self):
        """The the number of CV folds."""
        return type(self)._n_splits

    @n_splits.setter
    def n_splits(self, val):
        if not isinstance(val, int) and val > 0:
            raise TypeError("n_splits must be a positive integer")
        type(self)._n_splits = val

    def __init__(self):
        """The class constructor"""

        self.sklearn_settings = {
            "random_state": self.SEED,
        }

    def train_model(self, X: np.array, y: np.array) -> RidgeCV:
        """Ture and Train a Ridge Linear regression. y should be a vector."""

        alphas = np.linspace(0.0, 1.0, 21, endpoint=True)
        alphas[0] = 0.001

        reg = RidgeCV(
            alphas=alphas,
            scoring="r2",
            cv=self._n_splits,
        )

        return reg.fit(X, y)

    def apply_model(self, model, X: np.ma.MaskedArray) -> np.array:
        """Apply the trained model to the predictors and return the predicted 2D array."""

        _, height, width = X.shape

        nanmask = X.mask.any(axis=0) == False

        X = X[:, nanmask].T
        row_indices, col_indices = np.nonzero(nanmask)
        # X_idx = np.argwhere(nanmask)

        if len(X) > 250_000:
            # if the rows of X_fine are more than the prediction limit,
            # split the array into chunks to avoid having predict()
            # overflow the memory.
            n_splits = np.ceil(len(X) / self.MAX_PREDICTIONS)
            X = np.array_split(X, n_splits, axis=0)
            row_indices = [
                tuple(rows) for rows in np.array_split(row_indices, n_splits, axis=0)
            ]
            col_indices = [
                tuple(cols) for cols in np.array_split(col_indices, n_splits, axis=0)
            ]
        else:
            X, row_indices, col_indices, n_splits = [X], [row_indices], [col_indices], 1

        # Now reconstruct the 2D array
        chunck = 0
        for X, rows, cols in zip(X, row_indices, col_indices):

            predictions = model.predict(X)

            try:
                nvars = predictions.shape[1]
            except IndexError:
                nvars = 1
                predictions = predictions[:, np.newaxis]
            finally:
                shape = (nvars, height, width)

            if chunck == 0:
                arr = np.full(shape, fill_value=np.nan)

            for i in range(nvars):
                arr[i, rows, cols] = predictions[:, i]

            chunck += 1

        return arr
