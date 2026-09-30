"""Sectors: system-generated along terrain breaks, edited by the commander.

(P)MP Architecture v1.0 section 7.2. System-generated sectors split along ridgelines, drainages,
trails, and roads; the commander can edit them; manual creation and dragging a line to split a
sector are both wanted (Team answer, (P)MP v1.1 section 3.5). A redraw is a new ``sector`` row
version, never an update (C-01 draft, Proposed by AAR). Ranking is a stretch goal (I-06). Sweep
widths are a team item (I-14). How to split along terrain breaks, and sector size per operational
period, is Research (section 13).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Sector:
    """One sector version, in the shape of the C-01 draft ``sector`` row."""

    sector_id: str
    version: int
    geometry: dict[str, Any]  # GeoJSON polygon, WGS84
    valid_from: str  # UTC ISO-8601 ending in "Z"
    label: str | None = None
    properties: dict[str, Any] = field(default_factory=dict)


def generate_sectors(surface: Any, terrain: Any, target_count: int | None = None) -> list[Sector]:
    """Propose sectors from the probability surface (C-04) and the terrain package (C-05).

    Splits along ridgelines, drainages, trails, and roads. The proposal is what an ``override``
    event records when the commander changes it ((P)MP v1.1 section 6.5).
    """
    raise NotImplementedError("sector generation; waits on C-04, C-05, and the sector research")


def split_sector(sector: Sector, line: dict[str, Any], at: str) -> tuple[Sector, Sector]:
    """Split one sector along a drawn line (GeoJSON LineString) into two new versions."""
    raise NotImplementedError("sector editing; waits on R-10 for the drawing side")


def merge_sectors(a: Sector, b: Sector, at: str) -> Sector:
    """Merge two sectors into one new version."""
    raise NotImplementedError("sector editing; waits on R-10 for the drawing side")


def sum_surface_per_sector(surface: Any, sectors: list[Sector]) -> dict[str, float]:
    """The probability mass inside each sector, from the SPM surface (I-02)."""
    raise NotImplementedError("waits on C-04 (raster type, CRS, resolution)")
