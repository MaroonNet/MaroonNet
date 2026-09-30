"""Case checks run before anything is trained or scored.

Each rule either drops a case (with the reason recorded) or flags it. The
issues table is written next to the harmonized cases so every exclusion is
visible and reviewable.
"""

from __future__ import annotations

import math

import pandas as pd

from spm.schema import Case

EARTH_R_M = 6_371_008.8
MIN_DIST_M = 1.0  # find within 1 m of IPP: almost always a copied placeholder
MAX_DIST_M = 100_000.0  # beyond 100 km: likely a coordinate error, not a walk


def haversine_m(a, b) -> float:
    la1, lo1, la2, lo2 = map(math.radians, (a.lat, a.lon, b.lat, b.lon))
    h = (
        math.sin((la2 - la1) / 2) ** 2
        + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    )
    return 2 * EARTH_R_M * math.asin(math.sqrt(h))


def validate(cases: list[Case]) -> tuple[list[Case], pd.DataFrame]:
    """Return (cases kept, issues table with one row per dropped or flagged case)."""
    kept, issues, seen = [], [], {}

    def note(case_id: str, action: str, reason: str) -> None:
        issues.append({"case_id": case_id, "action": action, "reason": reason})

    for c in cases:
        if c.ipp is None or c.find is None:
            note(c.case_id, "drop", "missing IPP or find coordinates")
            continue
        if not (
            -90 <= c.ipp.lat <= 90
            and -180 <= c.ipp.lon <= 180
            and -90 <= c.find.lat <= 90
            and -180 <= c.find.lon <= 180
        ):
            note(c.case_id, "drop", "coordinates out of range")
            continue
        key = (round(c.ipp.lon, 5), round(c.ipp.lat, 5), round(c.find.lon, 5), round(c.find.lat, 5))
        if key in seen:
            note(c.case_id, "drop", f"duplicate of {seen[key]} (same IPP and find)")
            continue
        seen[key] = c.case_id
        d = haversine_m(c.ipp, c.find)
        if d < MIN_DIST_M:
            note(c.case_id, "drop", "find equals IPP (likely placeholder)")
            continue
        if d > MAX_DIST_M:
            note(
                c.case_id,
                "drop",
                f"IPP-find distance {d / 1000:.1f} km exceeds {MAX_DIST_M / 1000:.0f} km",
            )
            continue
        if c.category == "unknown":
            note(c.case_id, "flag", f"category unmapped (raw: {c.category_raw!r})")
        kept.append(c)
    return kept, pd.DataFrame(issues, columns=["case_id", "action", "reason"])
