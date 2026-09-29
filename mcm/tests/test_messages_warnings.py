import pytest

from mcm.field_warnings import rules
from mcm.mesh.gaps import Gap
from mcm.messages.catalog import CATALOG, airtime_cost_s, check_text, fits


def test_catalog_entries_fit_one_packet():
    for spec in CATALOG:
        assert fits(spec.typical_bytes), spec.name
        assert airtime_cost_s(spec, "LONG_FAST") > 0


def test_check_text():
    assert check_text("Return to CP") is None
    assert "bytes" in check_text("x" * 300)
    assert check_text("") == "empty message"


def test_buffer_overwrite_warning():
    quiet = [
        Gap(1, "2026-10-03T14:00:00Z", None, 16 * 60, "receive", 5, None),
        Gap(2, "2026-10-03T14:00:00Z", None, 5 * 60, "receive", 6, None),
    ]
    w = rules.buffer_overwrite(quiet)
    assert [x.node for x in w] == [1]


def test_unbuilt_rules_say_what_they_wait_on():
    with pytest.raises(NotImplementedError, match="P\\)MP"):
        rules.outside_sector()
    with pytest.raises(NotImplementedError):
        rules.losing_connectivity()
