"""Learned hybrid: ring prior x learned terrain multipliers, with regional partial pooling.

Score of a cell for a case in region r:

    s(cell) = log ring(cell) + sum over features f of  theta_r[f, bin_f(cell)]
    theta_r = w + delta_r

    w        shared log-multipliers, one per feature bin, pulled toward the
             published (prior-art) values by an L2 penalty lam_w
    delta_r  a per-region correction, pulled toward 0 by lam_region. A region
             with no cases (e.g. Colorado today) has delta = 0, so it gets the
             shared model; each case from that region nudges delta a little.

Fitting is a conditional logit over {find cell} + sampled "available" cells:
maximize the probability that the find cell wins against cells drawn
uniformly from the same window. This is the same estimator ecologists use for
resource selection functions (used vs. available points), and it stays
consistent when alternatives are sampled uniformly.

Out-of-range protection: feature ranges seen in training are recorded. At
prediction time, cells whose features fall outside them are flagged, and the
learned multipliers there fall back to the published ones.

Status: math and code tested on synthetic stacks only (tests/test_hybrid.py).
It says nothing about real behaviour until trained on real cases with real
terrain stacks (roadmap phase 4).
"""

from __future__ import annotations

from collections.abc import Callable

import numpy as np
from scipy.optimize import minimize
from scipy.special import logsumexp

from spm.features import relative
from spm.features.spec import FeatureSpec
from spm.geodata.grid import Window
from spm.models.bayes import apply_log_multipliers
from spm.models.ring import RingModel
from spm.schema import Case

StackProvider = Callable[[Case, Window], object]


class HybridModel:
    name = "hybrid"
    version = "1"

    def __init__(
        self,
        specs: list[FeatureSpec],
        stack_provider: StackProvider,
        prior: RingModel | None = None,
        side_m: float = 25_000,
        res: float = 100.0,
        n_alt: int = 2000,
        lam_w: float = 1.0,
        lam_region: float = 10.0,
        seed: int = 0,
    ):
        self.specs = specs
        self.stack_provider = stack_provider
        self.prior = prior or RingModel()
        self.side_m, self.res = side_m, res
        self.n_alt, self.lam_w, self.lam_region = n_alt, lam_w, lam_region
        self.rng = np.random.default_rng(seed)
        self.offsets = np.cumsum([0] + [s.n_bins for s in specs])
        self.K = int(
            self.offsets[-1]
        )  # real parameters; index K is a pinned zero (missing feature)
        self.w0 = np.concatenate([s.log_prior() for s in specs]) if specs else np.zeros(0)
        self.w = self.w0.copy()
        self.delta: dict[str, np.ndarray] = {}
        self.ranges: dict[str, tuple[float, float]] = {}
        self.n_train = 0

    # ---------- design ----------
    def _bins(self, feats: dict[str, np.ndarray], cells: np.ndarray | None = None) -> np.ndarray:
        """Global parameter index per (cell, feature); index K for a missing feature."""
        cols = []
        for f, s in enumerate(self.specs):
            if s.name in feats:
                v = feats[s.name].ravel() if cells is None else feats[s.name].ravel()[cells]
                cols.append(self.offsets[f] + s.bin_index(v))
            else:
                n = feats_size(feats) if cells is None else len(cells)
                cols.append(np.full(n, self.K))
        return np.stack(cols, axis=1).astype(np.int64)

    # ---------- training ----------
    def fit(self, cases: list[Case]):
        self.prior.fit(cases)
        data, regions, lo, hi = [], [], {}, {}
        for c in cases:
            if c.ipp is None or c.find is None:
                continue
            win = Window.around(c.ipp.lon, c.ipp.lat, side_m=self.side_m, res=self.res)
            find_rc = win.rowcol(c.find.lon, c.find.lat)
            stack = self.stack_provider(c, win)
            if find_rc is None or stack is None:
                continue
            feats = relative.compute(stack, win.rowcol(c.ipp.lon, c.ipp.lat))
            ring = self.prior.predict(c, win).prob
            n = win.n * win.n
            find_i = find_rc[0] * win.n + find_rc[1]
            alt = self.rng.choice(n - 1, size=min(self.n_alt, n - 1), replace=False)
            alt = alt + (alt >= find_i)  # skip the find cell
            cells = np.concatenate([[find_i], alt])
            logring = np.log(np.maximum(ring.ravel()[cells], 1e-300))
            data.append((logring, self._bins(feats, cells), c.region or "unknown"))
            regions.append(c.region or "unknown")
            for s in self.specs:
                if s.name in feats:
                    v = feats[s.name].ravel()[cells]
                    v = v[np.isfinite(v)]
                    if v.size:
                        lo[s.name] = min(lo.get(s.name, np.inf), float(v.min()))
                        hi[s.name] = max(hi.get(s.name, -np.inf), float(v.max()))
        self.n_train = len(data)
        self.ranges = {k: (lo[k], hi[k]) for k in lo}
        if not data or self.K == 0:
            return self

        reg_names = sorted(set(regions))
        n_reg, n_feat = len(reg_names), self.K
        ridx = {r: i for i, r in enumerate(reg_names)}

        def unpack(x):
            return x[:n_feat], x[n_feat:].reshape(n_reg, n_feat)

        def objective(x):
            w, d = unpack(x)
            gw, gd = np.zeros(n_feat + 1), np.zeros((n_reg, n_feat + 1))
            nll = 0.0
            for logring, idx, reg in data:
                r = ridx[reg]
                theta = np.append(w + d[r], 0.0)  # pinned zero at index K
                s = logring + theta[idx].sum(axis=1)
                lse = logsumexp(s)
                nll -= s[0] - lse
                p = np.exp(s - lse)
                g = -np.bincount(idx[0], minlength=n_feat + 1).astype(float)
                g += np.bincount(
                    idx.ravel(), weights=np.repeat(p, idx.shape[1]), minlength=n_feat + 1
                )
                gw += g
                gd[r] += g
            nll += self.lam_w * np.sum((w - self.w0) ** 2) + self.lam_region * np.sum(d**2)
            gw = gw[:n_feat] + 2 * self.lam_w * (w - self.w0)
            gd = gd[:, :n_feat] + 2 * self.lam_region * d
            return nll, np.concatenate([gw, gd.ravel()])

        x0 = np.concatenate([self.w0, np.zeros(n_reg * n_feat)])
        res = minimize(objective, x0, jac=True, method="L-BFGS-B")
        self.w, d = unpack(res.x)
        self.delta = {r: d[i] for r, i in ridx.items()}
        self.fit_result = res
        return self

    # ---------- inference ----------
    def multipliers(self, region: str | None = None) -> dict[str, np.ndarray]:
        """Learned multiplier per bin, per feature (exp of theta) for a region."""
        theta = self.w + self.delta.get(region, 0.0)
        return {
            s.name: np.exp(theta[self.offsets[f] : self.offsets[f + 1]])
            for f, s in enumerate(self.specs)
        }

    def predict(self, case, window, stack=None):
        ring = self.prior.predict(case, window)
        if stack is None or not self.specs:
            return apply_log_multipliers(ring, np.zeros(window.shape), self.name, self.version)
        feats = relative.compute(stack, window.rowcol(case.ipp.lon, case.ipp.lat))
        theta = np.append(self.w + self.delta.get(case.region, 0.0), 0.0)
        theta0 = np.append(self.w0, 0.0)
        idx = self._bins(feats).reshape(window.n, window.n, -1)

        flags = np.zeros(window.shape, bool)
        for s in self.specs:
            if s.name in feats and s.name in self.ranges:
                lo, hi = self.ranges[s.name]
                v = feats[s.name]
                flags |= np.isfinite(v) & ((v < lo) | (v > hi))
        logm = np.where(flags, theta0[idx].sum(-1), theta[idx].sum(-1))
        pred = apply_log_multipliers(ring, logm, self.name, self.version)
        pred.flags = flags
        return pred


def feats_size(feats: dict[str, np.ndarray]) -> int:
    return next(iter(feats.values())).size
