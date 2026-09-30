"""Mesh coverage model: which places can hear a radio at a given place (MCM v1.1 sections 3.3, 6.4).

Co-owned with (P)MP. The same code runs on planned positions ((P)MP, pre-mission) and on live
positions (MCM). Where the split between the two owners falls is Open (MCM v1.1 section 9 Q1), so
this module fixes only the interface and one deliberately naive baseline.

The interface: a model takes a transmitter site and receiver points and returns a Link per point,
with a predicted received power and a class (covered, marginal, shadow). The build order in MCM
v1.1 section 6.4 (elevation grid, line of sight, Fresnel zone, foliage, diffraction) adds terrain
behind the same interface. Validation against SPLAT! and against observed reception (validate.py)
calls the interface, so a better model drops in without changing the harness.

The baseline, FreeSpaceModel, ignores terrain and foliage entirely. It is an upper bound on range
and exists so the harness and the tests have something to run. Do not quote its ranges.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Protocol

CLASSES = ("covered", "marginal", "shadow")
EARTH_RADIUS_M = 6_371_008.8


@dataclass(frozen=True)
class Site:
    lat: float
    lon: float
    antenna_agl_m: float = 1.5  # height above ground; a pole or a drone is just a larger value
    alt_m: float | None = None  # ground elevation, when the model uses terrain


@dataclass(frozen=True)
class RadioParams:
    """Link budget inputs. Every default is a placeholder to replace from datasheets and tests."""

    tx_power_dbm: float = 22.0  # SX1262 maximum; the configured value may be lower
    tx_gain_dbi: float = 0.0
    rx_gain_dbi: float = 0.0
    frequency_mhz: float = 915.0
    sensitivity_dbm: float = -130.0  # depends on the preset; Research
    marginal_margin_db: float = 10.0  # within this many dB of sensitivity counts as marginal


@dataclass(frozen=True)
class Link:
    rx: Site
    distance_m: float
    path_loss_db: float
    rx_power_dbm: float
    link_class: str


class CoverageModel(Protocol):
    """Anything that predicts links from one transmitter to many receiver points."""

    def predict(self, tx: Site, rx_points: list[Site], radio: RadioParams) -> list[Link]: ...


def distance_m(a: Site, b: Site) -> float:
    """Great-circle distance in meters (haversine)."""
    p1, p2 = math.radians(a.lat), math.radians(b.lat)
    dp = p2 - p1
    dl = math.radians(b.lon - a.lon)
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * EARTH_RADIUS_M * math.asin(math.sqrt(h))


def free_space_loss_db(distance_m_: float, frequency_mhz: float) -> float:
    """Free-space path loss: 20 log10(d_km) + 20 log10(f_MHz) + 32.44."""
    d_km = max(distance_m_, 1.0) / 1000.0
    return 20 * math.log10(d_km) + 20 * math.log10(frequency_mhz) + 32.44


def classify(rx_power_dbm: float, radio: RadioParams) -> str:
    if rx_power_dbm < radio.sensitivity_dbm:
        return "shadow"
    if rx_power_dbm < radio.sensitivity_dbm + radio.marginal_margin_db:
        return "marginal"
    return "covered"


class FreeSpaceModel:
    """Baseline: free-space loss only. No terrain, no foliage. An upper bound, not a prediction."""

    def predict(self, tx: Site, rx_points: list[Site], radio: RadioParams) -> list[Link]:
        links = []
        for rx in rx_points:
            d = distance_m(tx, rx)
            loss = free_space_loss_db(d, radio.frequency_mhz)
            p = radio.tx_power_dbm + radio.tx_gain_dbi + radio.rx_gain_dbi - loss
            links.append(Link(rx, d, loss, p, classify(p, radio)))
        return links
