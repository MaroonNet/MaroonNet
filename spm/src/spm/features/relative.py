"""Relative terrain features: the only kind of feature SPM models may use.

A relative feature describes a cell in terms that mean the same thing in
Arizona, Yosemite, New York or Colorado: distance to the nearest trail,
elevation gained or lost since the IPP, whether the cell is in the IPP's
watershed. Absolute values (latitude, raw elevation, region name) are banned
as model inputs because they let a model memorize the regions it was trained
on instead of learning behaviour that transfers.

All functions are pure: arrays in, arrays out, no I/O.
"""

from __future__ import annotations

import numpy as np
from scipy import ndimage

from spm.geodata.stack import FeatureStack

# name -> (unit, what it means). The model feature list is drawn from these.
FEATURES = {
    "elev_change_m": ("m", "cell elevation minus IPP elevation (+ = uphill)"),
    "slope_deg": ("deg", "local slope"),
    "tpi_m": ("m", "topographic position: + ridge/high ground, - drainage/valley"),
    "dist_trail_m": ("m", "distance to nearest trail cell"),
    "dist_road_m": ("m", "distance to nearest road cell"),
    "dist_stream_m": ("m", "distance to nearest stream/drainage cell"),
    "same_watershed": ("0/1", "1 if the cell is in the IPP's watershed unit"),
}


def elevation_change(dem: np.ndarray, ipp_rc: tuple[int, int]) -> np.ndarray:
    return dem - dem[ipp_rc]


def slope_deg(dem: np.ndarray, res: float) -> np.ndarray:
    gy, gx = np.gradient(dem, res)
    return np.degrees(np.arctan(np.hypot(gx, gy)))


def tpi(dem: np.ndarray, res: float, radius_m: float = 300.0) -> np.ndarray:
    """Cell elevation minus mean elevation within ~radius_m (square neighbourhood)."""
    size = max(3, int(round(2 * radius_m / res)) | 1)
    return dem - ndimage.uniform_filter(dem, size=size, mode="nearest")


def distance_to(mask: np.ndarray, res: float) -> np.ndarray:
    """Euclidean distance (m) from each cell to the nearest True cell; inf if none."""
    if not mask.any():
        return np.full(mask.shape, np.inf)
    return ndimage.distance_transform_edt(~mask.astype(bool)) * res


def same_watershed(ws: np.ndarray, ipp_rc: tuple[int, int]) -> np.ndarray:
    return (ws == ws[ipp_rc]).astype(float)


def compute(stack: FeatureStack, ipp_rc: tuple[int, int]) -> dict[str, np.ndarray]:
    """Every relative feature the stack's layers allow, keyed by FEATURES names."""
    res = stack.window.res
    out: dict[str, np.ndarray] = {}
    if stack.has("dem"):
        dem = stack["dem"].astype(float)
        out["elev_change_m"] = elevation_change(dem, ipp_rc)
        out["slope_deg"] = slope_deg(dem, res)
        out["tpi_m"] = tpi(dem, res)
    for layer, name in (
        ("trail_mask", "dist_trail_m"),
        ("road_mask", "dist_road_m"),
        ("stream_mask", "dist_stream_m"),
    ):
        if stack.has(layer):
            out[name] = distance_to(stack[layer], res)
    if stack.has("watershed_id") and stack["watershed_id"][ipp_rc] != 0:
        out["same_watershed"] = same_watershed(stack["watershed_id"], ipp_rc)
    return out
