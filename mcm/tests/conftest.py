import json
from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def lib_packets() -> dict:
    """Hand-built library-shaped packet dicts, keyed by case name."""
    return json.loads((FIXTURES / "library_packets.json").read_text(encoding="utf-8"))
