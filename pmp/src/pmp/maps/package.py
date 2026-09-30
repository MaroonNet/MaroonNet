"""The terrain layer package: which files a mission region needs on disk, and its manifest.

This is (P)MP's draft of contract C-05 ((P)MP Architecture v1.0 section 6.2, item PM-04). (P)MP
writes; SPM and MCM sign; blocked by R-05 (who downloads) and R-06 (the region). The map draws
the files; SPM reads elevation and land cover for its terrain factors; the coverage model reads
them for line of sight and foliage.

The manifest records the coordinate reference system. SPM's ``Window`` works in the local UTM
zone (EPSG:32613 for Colorado), so the map, the model, and the coverage grid line up when the
manifest names the same zone. Where the package lives on disk, and how a copied mission finds it
for an AAR on another machine, is A-04 (Open, with Corey).
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

PACKAGE_SCHEMA = "pmp.terrain_package/0.1-draft"

# (P)MP Architecture v1.0 section 6.2, in its order.
LAYER_KINDS = ("basemap", "elevation", "landcover", "trails", "watersheds")


@dataclass(frozen=True)
class TerrainLayer:
    """One file in the package."""

    kind: str  # one of LAYER_KINDS
    rel_path: str  # relative to the package folder
    format: str  # pmtiles | mbtiles | geotiff | geojson | gpkg
    source: str  # OpenStreetMap, USGS 3DEP, NLCD, ESA WorldCover, USGS WBD, ...
    produced_at: str  # UTC ISO-8601 ending in "Z"
    sha256: str | None = None
    resolution_m: float | None = None

    def __post_init__(self) -> None:
        if self.kind not in LAYER_KINDS:
            raise ValueError(f"unknown layer kind {self.kind!r}; expected one of {LAYER_KINDS}")


@dataclass(frozen=True)
class TerrainPackage:
    """The manifest: one region, its CRS, and its layers."""

    region: str  # a name the commander picks
    bbox: tuple[float, float, float, float]  # west, south, east, north, WGS84 degrees
    crs: str  # the local UTM zone, e.g. "EPSG:32613"
    cell_m: float  # the analysis cell size the model and the coverage grid share
    layers: tuple[TerrainLayer, ...] = ()
    produced_at: str | None = None
    schema: str = PACKAGE_SCHEMA
    extra: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if len(self.bbox) != 4:
            raise ValueError("bbox must be (west, south, east, north)")
        if self.schema != PACKAGE_SCHEMA:
            raise ValueError(f"schema {self.schema!r} is not {PACKAGE_SCHEMA!r}")

    def to_dict(self) -> dict[str, Any]:
        """The manifest as a JSON-safe dict."""
        data = asdict(self)
        data["bbox"] = list(self.bbox)
        data["layers"] = [asdict(layer) for layer in self.layers]
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TerrainPackage:
        """Rebuild a manifest from ``to_dict`` output."""
        data = dict(data)
        data["bbox"] = tuple(data["bbox"])
        data["layers"] = tuple(TerrainLayer(**layer) for layer in data.get("layers", ()))
        return cls(**data)

    def to_json(self) -> str:
        """The manifest as JSON, keys sorted, indented for people."""
        return json.dumps(self.to_dict(), sort_keys=True, indent=2)

    @classmethod
    def from_json(cls, text: str) -> TerrainPackage:
        """Parse ``to_json`` output."""
        return cls.from_dict(json.loads(text))


def write_manifest(package: TerrainPackage, folder: Path) -> Path:
    """Write ``manifest.json`` into the package folder and return its path."""
    raise NotImplementedError("manifest write; waits on the on-disk location (A-04, R-05)")


def read_manifest(folder: Path) -> TerrainPackage:
    """Read ``manifest.json`` from a package folder and check that every file is present."""
    raise NotImplementedError("manifest read; waits on the on-disk location (A-04, R-05)")
