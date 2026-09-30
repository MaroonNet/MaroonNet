"""Score several models on the same cases with the same splits.

Every model is refit for each fold so a case never helps predict itself.
Output: one row per (model, case), plus a summary table with the mean
MapScore and a bootstrap 95% confidence interval per model.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator

import numpy as np
import pandas as pd

from spm.eval.mapscore import score
from spm.geodata.grid import MAPSCORE_SIDE_M, Window
from spm.schema import Case


def leave_one_out(cases: list[Case]) -> Iterator[tuple[list[Case], Case]]:
    for i, test in enumerate(cases):
        yield cases[:i] + cases[i + 1 :], test


def leave_one_region_out(cases: list[Case]) -> Iterator[tuple[list[Case], Case]]:
    """For when several regions exist: train on the others, test on each held-out region."""
    for c in cases:
        train = [t for t in cases if t.region != c.region]
        if train:
            yield train, c


SPLITS = {"loo": leave_one_out, "loro": leave_one_region_out}


def evaluate(
    models: dict[str, Callable[[], object]],
    cases: list[Case],
    split: str = "loo",
    res: float = 25.0,
    side_m: float = MAPSCORE_SIDE_M,
    stack_provider: Callable[[Case, Window], object] | None = None,
) -> pd.DataFrame:
    """``stack_provider(case, window)`` returns the terrain FeatureStack (or None) for a case."""
    rows = []
    folds = list(SPLITS[split](cases))
    for name, factory in models.items():
        for train, test in folds:
            model = factory().fit(train)
            window = Window.around(test.ipp.lon, test.ipp.lat, side_m=side_m, res=res)
            stack = stack_provider(test, window) if stack_provider else None
            pred = model.predict(test, window, stack)
            pred.check()
            rows.append(
                {
                    "model": name,
                    "case_id": test.case_id,
                    "category": test.category,
                    "region": test.region,
                    "find_in_window": window.rowcol(test.find.lon, test.find.lat) is not None,
                    "p_outside": round(pred.p_outside, 4),
                    "mapscore": score(pred, test),
                    "has_stack": stack is not None,
                }
            )
    return pd.DataFrame(rows)


def summarize(per_case: pd.DataFrame, n_boot: int = 2000, seed: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    out = []
    for name, g in per_case.groupby("model", sort=False):
        s = g["mapscore"].to_numpy()
        boots = rng.choice(s, size=(n_boot, len(s)), replace=True).mean(axis=1)
        out.append(
            {
                "model": name,
                "n_cases": len(s),
                "mean_mapscore": s.mean(),
                "ci95_low": np.percentile(boots, 2.5),
                "ci95_high": np.percentile(boots, 97.5),
                "median": np.median(s),
                "mean_in_window_only": g.loc[g["find_in_window"], "mapscore"].mean(),
                "finds_outside_window": int((~g["find_in_window"]).sum()),
            }
        )
    return pd.DataFrame(out).round(3)
