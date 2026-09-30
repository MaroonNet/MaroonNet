"""Commands to the field: text and waypoints through MCM's ``Gateway`` (I-09).

(P)MP Architecture v1.0 section 5.5. The daemon calls ``Gateway.send_text(text, channel, dest)``;
waypoints and, later, custom message types follow the same path. The gateway refuses a message
that does not fit one packet. Outbound sends are recorded by the daemon as ``message`` rows with
``direction = out`` (Proposed by MCM Architecture v1.0 section 4.7). What v1 sends and its
airtime cost is C-07 (MCM writes, (P)MP signs). Sector polygons need a custom app and are not v1.
"""

from __future__ import annotations

from typing import Any

BROADCAST = 0xFFFFFFFF  # Meshtastic broadcast destination


def send_text(gateway: Any, text: str, channel: int = 0, dest: int = BROADCAST) -> None:
    """Send one text message and record it as an outbound ``message`` row."""
    raise NotImplementedError("outbound text; waits on C-07 and the Gateway API (MCM section 4.7)")


def send_waypoint(
    gateway: Any,
    name: str,
    lat: float,
    lon: float,
    channel: int = 0,
    dest: int = BROADCAST,
) -> None:
    """Send one waypoint to the stock Meshtastic app and record it as an outbound row."""
    raise NotImplementedError("outbound waypoint; waits on C-07 and the Gateway API")
