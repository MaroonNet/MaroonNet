"""Predicted against observed reception (MCM v1.1 section 6.5).

The daemon logs SNR and RSSI on every packet. For each position a radio reported, the model
predicts a class for the link to the gateway; the log says whether the gateway heard it directly.
The v2.2 target was agreement three times in four. That target is not a decision.

Two rules keep the comparison honest:

- Only packets heard directly (hops_taken == 0) say anything about the origin's own link. A relayed
  packet's SNR and RSSI describe the relay's link, not the origin's.
- A packet that never arrived is invisible in the log. Missed reception shows up as gaps
  (mesh/gaps.py), not as rows, so observed "shadow" comes from gaps, not from low RSSI.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from mcm.contract.record import RadioRecord
from mcm.coverage.model import CoverageModel, RadioParams, Site


@dataclass(frozen=True)
class Comparison:
    seq: int
    node: int
    predicted: str
    observed_rssi: int | None
    observed_snr: float | None
    agrees: bool


def direct_positions(records: Iterable[RadioRecord]) -> list[RadioRecord]:
    """Position records the gateway heard straight from the origin radio."""
    return [
        r
        for r in records
        if r.kind == "position" and r.position is not None and r.header.heard_directly
    ]


def compare(
    records: Iterable[RadioRecord],
    gateway: Site,
    model: CoverageModel,
    radio: RadioParams,
    antenna_agl_m: float = 1.5,
) -> list[Comparison]:
    """For each directly heard position, did the model predict the gateway could hear it?"""
    out = []
    for r in direct_positions(records):
        assert r.position is not None
        site = Site(r.position.lat, r.position.lon, antenna_agl_m, r.position.alt_m)
        link = model.predict(site, [gateway], radio)[0]
        out.append(
            Comparison(
                seq=r.seq,
                node=r.header.from_node,
                predicted=link.link_class,
                observed_rssi=r.header.rx_rssi,
                observed_snr=r.header.rx_snr,
                agrees=link.link_class != "shadow",  # it was heard, so shadow is a miss
            )
        )
    return out


def agreement(comparisons: list[Comparison]) -> float | None:
    """Share of comparisons where the prediction agrees with what was heard."""
    if not comparisons:
        return None
    return sum(c.agrees for c in comparisons) / len(comparisons)
