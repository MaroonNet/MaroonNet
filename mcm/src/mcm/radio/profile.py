"""Load the radio profile (configs/radio_profile.toml): firmware pin, gateway, LoRa, position."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path

DEFAULT_PROFILE = Path(__file__).resolve().parents[3] / "configs" / "radio_profile.toml"


@dataclass(frozen=True)
class RadioProfile:
    firmware_version: str
    python_library: str
    pinned_on: str
    board: str
    transport: str
    port: str
    gateway_role: str
    region: str
    modem_preset: str
    hop_limit: int
    broadcast_interval_s: int
    smart_broadcast: bool
    gap_factor: float

    @property
    def is_pinned(self) -> bool:
        """True once the team has recorded a firmware version and a library version."""
        return bool(self.firmware_version and self.python_library)

    @property
    def gap_threshold_s(self) -> float:
        """Silence longer than this, between two reports from one radio, is a gap."""
        return self.gap_factor * self.broadcast_interval_s


def load(path: str | Path = DEFAULT_PROFILE) -> RadioProfile:
    """Read a radio profile TOML file."""
    with open(path, "rb") as fh:
        d = tomllib.load(fh)
    fw, gw, lora, pos = d["firmware"], d["gateway"], d["lora"], d["position"]
    return RadioProfile(
        firmware_version=fw.get("version", ""),
        python_library=fw.get("python_library", ""),
        pinned_on=fw.get("pinned_on", ""),
        board=fw.get("board", ""),
        transport=gw.get("transport", "serial"),
        port=gw.get("port", ""),
        gateway_role=gw.get("role", ""),
        region=lora.get("region", "US"),
        modem_preset=lora["modem_preset"],
        hop_limit=int(lora.get("hop_limit", 3)),
        broadcast_interval_s=int(pos["broadcast_interval_s"]),
        smart_broadcast=bool(pos.get("smart_broadcast", False)),
        gap_factor=float(pos.get("gap_factor", 3.0)),
    )


def check_firmware(profile: RadioProfile, reported: str | None) -> str | None:
    """Compare the gateway's reported firmware with the pin. Returns a problem, or None if fine.

    Mixed versions cause packet-format mismatches that look like radio faults (MCM v1.1 section
    6.3), so the gateway reports this loudly on connect.
    """
    if not profile.is_pinned:
        return "firmware is not pinned yet (configs/radio_profile.toml); record it before field use"
    if not reported:
        return "gateway did not report a firmware version"
    if reported != profile.firmware_version:
        return f"gateway firmware {reported} does not match the pin {profile.firmware_version}"
    return None
