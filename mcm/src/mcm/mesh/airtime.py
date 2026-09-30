"""Airtime math: time on air per packet, and how busy the channel gets (MCM v1.1 section 6.1).

    busy seconds per hour = N x (3600 / I) x T x H
    utilization           = busy seconds per hour / 3600

N nodes, I report interval in seconds, T time on air of one packet, H transmissions per packet
(the doc takes the hop limit, 3 by default, as the estimate). T comes from the Semtech LoRa
time-on-air formula (SX1261/2 datasheet, section 6.1.4) with the preset's spreading factor,
bandwidth, and coding rate.

Estimates only. The preset table and the 16-symbol preamble are from Meshtastic documentation and
firmware source; check both against the pinned firmware before any figure is quoted. H is a
simplification: managed flooding cancels some rebroadcasts, and more nodes in earshot can mean more.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class Preset:
    name: str
    bandwidth_hz: float
    spreading_factor: int
    coding_rate: int  # the x in 4/x


# Meshtastic modem presets (meshtastic.org, Radio Settings). Verify against the pinned firmware.
PRESETS: dict[str, Preset] = {
    p.name: p
    for p in (
        Preset("SHORT_TURBO", 500e3, 7, 5),
        Preset("SHORT_FAST", 250e3, 7, 5),
        Preset("SHORT_SLOW", 250e3, 8, 5),
        Preset("MEDIUM_FAST", 250e3, 9, 5),
        Preset("MEDIUM_SLOW", 250e3, 10, 5),
        Preset("LONG_TURBO", 500e3, 11, 8),
        Preset("LONG_FAST", 250e3, 11, 5),
        Preset("LONG_MODERATE", 125e3, 11, 8),
        Preset("LONG_SLOW", 125e3, 12, 8),
    )
}

PREAMBLE_SYMBOLS = 16  # Meshtastic firmware; LoRa default is 8
MAX_PAYLOAD_BYTES = 233  # data payload per packet, MCM v1.1 section 3.5

# Firmware congestion behavior, MCM v1.1 section 6.1 (estimates; confirm in the firmware source).
DELAY_THRESHOLD = 0.25
THROTTLE_THRESHOLD = 0.40


def time_on_air_s(preset: Preset | str, payload_bytes: int) -> float:
    """Seconds one packet of payload_bytes (over the air, header included) occupies the channel."""
    p = PRESETS[preset] if isinstance(preset, str) else preset
    sf, bw, cr = p.spreading_factor, p.bandwidth_hz, p.coding_rate
    t_sym = (2**sf) / bw
    low_dr_opt = 1 if t_sym > 0.016 else 0  # required above 16 ms per symbol
    explicit_header = 0  # H = 0 means the header is present
    crc = 1
    numerator = 8 * payload_bytes - 4 * sf + 28 + 16 * crc - 20 * explicit_header
    payload_symbols = 8 + max(math.ceil(numerator / (4 * (sf - 2 * low_dr_opt))) * cr, 0)
    preamble_s = (PREAMBLE_SYMBOLS + 4.25) * t_sym
    return preamble_s + payload_symbols * t_sym


def utilization(
    nodes: int,
    interval_s: float,
    preset: Preset | str,
    payload_bytes: int = 50,
    transmissions_per_packet: float = 3,
) -> float:
    """Fraction of each hour the channel is busy with position reports (0.32 means 32%)."""
    t = time_on_air_s(preset, payload_bytes)
    busy_per_hour = nodes * (3600.0 / interval_s) * t * transmissions_per_packet
    return busy_per_hour / 3600.0


def max_nodes(
    interval_s: float,
    preset: Preset | str,
    ceiling: float = DELAY_THRESHOLD,
    payload_bytes: int = 50,
    transmissions_per_packet: float = 3,
) -> int:
    """The largest node count that stays at or under the ceiling. Feeds the spacing rule."""
    per_node = utilization(1, interval_s, preset, payload_bytes, transmissions_per_packet)
    return int(ceiling // per_node)


def status(u: float) -> str:
    """Plain-language reading of a utilization figure."""
    if u >= THROTTLE_THRESHOLD:
        return "throttled"
    if u >= DELAY_THRESHOLD:
        return "delayed"
    return "ok"
