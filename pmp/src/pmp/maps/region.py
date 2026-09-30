"""The select-a-region step: download and build one region's terrain package before a mission.

(P)MP Architecture v1.0 section 7.5, from the pipeline in (P)MP v1.1 section 6.4:

1. Download an OpenStreetMap extract for the region (Geofabrik publishes state-level extracts).
2. Run Planetiler on it; one file of vector tiles (PMTiles or MBTiles) in one pass.
3. Download elevation from USGS 3DEP (10 m or 30 m GeoTIFF); derive contours or hillshade.
4. Download land cover (NLCD for the US; ESA WorldCover for anywhere) as GeoTIFF.
5. Serve all of it from the backend to the map library in the browser.

A statewide tile build takes hours and elevation rasters run to tens of gigabytes, so a
select-a-region step at first run limits this to what the commander needs (Proposed). A
Planetiler run on one small region is work the owner can start with no decision (Architecture
v1.0 section 7.2). The region for the fall slice follows the reference case SPM picks (R-06).
"""

from __future__ import annotations

from pathlib import Path

from pmp.maps.package import TerrainPackage


def select_region(
    name: str, bbox: tuple[float, float, float, float], cell_m: float
) -> TerrainPackage:
    """Start a package for a region: name, bounding box (west, south, east, north), the UTM zone."""
    raise NotImplementedError("region step; waits on R-05 and R-06")


def build_basemap(package: TerrainPackage, osm_extract: Path, out: Path) -> Path:
    """Run Planetiler on an OpenStreetMap extract; one PMTiles or MBTiles file for the region."""
    raise NotImplementedError("Planetiler run; the owner's first experiment (section 12.1)")


def fetch_elevation(package: TerrainPackage, out: Path, resolution_m: int = 10) -> Path:
    """Download USGS 3DEP elevation for the bbox as GeoTIFF."""
    raise NotImplementedError("waits on R-05")


def fetch_landcover(package: TerrainPackage, out: Path, source: str = "NLCD") -> Path:
    """Download NLCD (US) or ESA WorldCover land cover for the bbox as GeoTIFF."""
    raise NotImplementedError("waits on R-05")
