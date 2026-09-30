"""Radio spacing: from team size, radio count, and the MCM node limit (I-10).

(P)MP Architecture v1.0 section 7.4. Computed here from team size and radio count; sent to MCM to
work in tandem (Team answer, (P)MP v1.1 section 3.5). The MCM node limit for a preset and interval,
``mcm.mesh.airtime.max_nodes``, feeds the rule; MCM's airtime math is in MCM Architecture v1.0
section 6.2. Sweep widths and coverage rates stay parked (I-14). Terrain cuts Meshtastic range,
so the terrain selected for a plan bears on where radios can be placed (Team answer).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SpacingPlan:
    """What (P)MP hands MCM: how many radios, how far apart, and the limit they fit under."""

    team_size: int
    radio_count: int
    max_nodes: int  # from MCM for the chosen preset and interval
    spacing_m: float | None  # None until sweep widths (I-14) and a field-tested range (M-04) exist
    note: str | None = None


def radio_spacing(team_size: int, radio_count: int, max_nodes: int) -> SpacingPlan:
    """The spacing rule. Refuses a plan with more radios than the node limit carries."""
    raise NotImplementedError(
        "spacing rule; waits on I-14 (sweep widths) and the preset and interval field test (M-04)"
    )
