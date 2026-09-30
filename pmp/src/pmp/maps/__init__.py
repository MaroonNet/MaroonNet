"""Maps: the terrain layer package (C-05) and the select-a-region step.

(P)MP Architecture v1.0 sections 6.2 and 7.5. Map and tile loading is (P)MP (Verified V-13).
The base map, elevation, and land cover are downloaded per region before the mission, while
connected; maps are not pre-built (Team answer, (P)MP v1.1 section 3.1). SPM and the co-owned
coverage model read the same files (I-03). Which segment downloads and stores them is Open (R-05).
"""

from pmp.maps.package import TerrainLayer, TerrainPackage

__all__ = ["TerrainLayer", "TerrainPackage"]
