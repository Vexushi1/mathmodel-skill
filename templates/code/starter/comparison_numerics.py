"""Small polynomial example; replace the model before using real project data."""
from __future__ import annotations

import numpy as np


def fit_polynomial(t, y, degree, method, evaluation_t):
    t, y = np.asarray(t, dtype=float), np.asarray(y, dtype=float)
    if t.ndim != 1 or t.shape != y.shape or not np.isfinite(t).all() or not np.isfinite(y).all():
        raise ValueError("Finite paired training vectors are required")
    design = np.vander(t, degree + 1, increasing=True)
    if method == "QR":
        q, r = np.linalg.qr(design, mode="reduced")
        if np.min(np.abs(np.diag(r))) <= np.finfo(float).eps * np.linalg.norm(r):
            raise ValueError("QR design is rank deficient")
        coefficients = np.linalg.solve(r, q.T @ y)
    elif method == "SVD":
        u, singular, vh = np.linalg.svd(design, full_matrices=False)
        if singular[-1] <= np.finfo(float).eps * max(design.shape) * singular[0]:
            raise ValueError("SVD design is rank deficient")
        coefficients = vh.T @ ((u.T @ y) / singular)
    else:
        raise ValueError("This example supports explicit QR or SVD only")
    evaluation = np.vander(np.asarray(evaluation_t, dtype=float), degree + 1, increasing=True)
    prediction = evaluation @ coefficients
    residual = design @ coefficients - y
    normal_residual = float(np.max(np.abs(design.T @ residual)))
    if not np.isfinite(coefficients).all() or not np.isfinite(prediction).all():
        raise ValueError("Nonfinite polynomial result")
    return coefficients.tolist(), prediction.tolist(), normal_residual
