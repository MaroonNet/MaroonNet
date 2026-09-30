"""The daemon message: what the bridge daemon pushes to the screen, and when.

This is (P)MP's draft of contract C-02 ((P)MP Architecture v1.0 section 5.4, item PM-02). AAR and
MCM sign it. The message list is drafted here; the transport (WebSocket, server-sent events, or
polling) waits on the backend framework (R-03).

Rules the message keeps:

- Every message carries its kind, the host clock time (UTC ISO-8601 ending in "Z"), and a
  sequence number that rises by one per daemon session, so a screen that reconnects can ask for
  what it missed.
- The payload holds only what the row it announces holds. Nothing is invented: no interpolated
  position, no filled-in time.
- The message carries its schema string. A reader refuses a message with a different one.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any

# Bumped when the message shape changes. Written into every message so a reader can tell.
MESSAGE_SCHEMA = "pmp.daemon_message/0.1-draft"

# Section 5.4 of the architecture document, in the order the table lists them.
KINDS = ("node_seen", "position", "telemetry", "message", "quiet_node", "gap", "mission")


@dataclass(frozen=True)
class DaemonMessage:
    """One push from the daemon to the screen."""

    kind: str
    time: str  # host clock, UTC ISO-8601 ending in "Z"
    seq: int  # per daemon session, rising by one
    payload: dict[str, Any] = field(default_factory=dict)
    schema: str = MESSAGE_SCHEMA

    def __post_init__(self) -> None:
        if self.kind not in KINDS:
            raise ValueError(f"unknown message kind {self.kind!r}; expected one of {KINDS}")
        if self.schema != MESSAGE_SCHEMA:
            raise ValueError(f"schema {self.schema!r} is not {MESSAGE_SCHEMA!r}")

    def to_dict(self) -> dict[str, Any]:
        """The message as a JSON-safe dict."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DaemonMessage:
        """Rebuild a message from ``to_dict`` output. Refuses a different schema string."""
        return cls(**data)

    def to_json(self) -> str:
        """One line of JSON, keys sorted, for a push channel or a capture file."""
        return json.dumps(self.to_dict(), sort_keys=True)

    @classmethod
    def from_json(cls, line: str) -> DaemonMessage:
        """Parse one line written by ``to_json``."""
        return cls.from_dict(json.loads(line))
