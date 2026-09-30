"""Planned-position coverage: (P)MP's call into the co-owned coverage model (C-06, I-11).

(P)MP Architecture v1.0 section 6.3. (P)MP runs the model on planned positions pre-mission; MCM
runs it live against current positions; same code (Team answer, MCM v1.1 section 3.3). The
interface lives in ``mcm.coverage.model`` (MCM Architecture v1.0 section 6.3) with a free-space
baseline whose ranges are not to be quoted. Where the pen sits for the terrain steps is Open
(R-08, M-05; Elijah and Diego). The output format to the screen is Open.

Nothing from ``mcm`` is imported here. The model is handed in, so this package depends on the
interface, not the package.
"""

from __future__ import annotations

from typing import Any

from pmp.contract.mission_input import LatLon


def planned_coverage(
    positions: list[LatLon],
    terrain: Any,
    model: Any,
) -> Any:
    """Per-cell coverage classes for planned radio positions, from the C-06 interface.

    ``terrain`` is the C-05 package (elevation and land cover); ``model`` is an object with the
    ``mcm.coverage.model`` interface. The result is the overlay the planning view draws.
    """
    raise NotImplementedError("coverage call; waits on C-06 (R-08) and C-05")
