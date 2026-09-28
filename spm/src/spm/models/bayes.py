"""Prior-art model: ring prior x published terrain multipliers (no training).

    P(cell) proportional to ring(cell) x product over features of multiplier[bin of cell]

This is the Bayesian combination step of SPM v1.1 §3.1, built only from
published numbers (Koester 2008 rings; Doke 2012 / Sava et al. 2016 watershed;
Jacobs 2015 terrain multipliers). It is the fall deliverable and the baseline
the learned hybrid has to beat.

Features whose multipliers are not filled in configs/prior_art.yaml are
skipped, so with an empty config this model equals the ring model.
"""

from __future__ import annotations

import numpy as np

from spm.features import relative
from spm.features.spec import FeatureSpec
from spm.models.ring import RingModel
from spm.schema import Prediction


def apply_log_multipliers(
    ring: Prediction, logm: np.ndarray, name: str, version: str
) -> Prediction:
    """Reweight a ring prediction by exp(logm), keeping the ring's in-window mass."""
    inside = 1.0 - ring.p_outside
    w = ring.prob * np.exp(logm - logm.max())
    total = w.sum()
    prob = w * (inside / total) if total > 0 else ring.prob
    return Prediction(
        prob=prob, window=ring.window, model=name, model_version=version, p_outside=ring.p_outside
    )


class BayesModel:
    name = "bayes_prior_art"
    version = "1"

    def __init__(self, specs: list[FeatureSpec], prior: RingModel | None = None):
        self.specs = [s for s in specs if s.prior_complete]
        self.prior = prior or RingModel()

    def fit(self, cases):
        self.prior.fit(cases)  # only the ring distances are fitted; multipliers are published
        return self

    def predict(self, case, window, stack=None):
        ring = self.prior.predict(case, window)
        if stack is None or not self.specs:
            return apply_log_multipliers(ring, np.zeros(window.shape), self.name, self.version)
        ipp_rc = window.rowcol(case.ipp.lon, case.ipp.lat)
        feats = relative.compute(stack, ipp_rc)
        logm = np.zeros(window.shape)
        for s in self.specs:
            if s.name in feats:
                logm += s.log_prior()[s.bin_index(feats[s.name])]
        return apply_log_multipliers(ring, logm, self.name, self.version)
