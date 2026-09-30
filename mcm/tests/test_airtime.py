import pytest

from mcm.mesh import airtime

# MCM v1.1 section 6.1 table: (nodes, interval, LongFast %, MediumFast %)
DOC_TABLE = [
    (5, 60, 16, 5),
    (10, 60, 32, 9),
    (20, 60, 64, 18),
    (10, 120, 16, 5),
    (20, 120, 32, 9),
    (20, 180, 21, 6),
]


def test_time_on_air_matches_doc_estimates():
    assert airtime.time_on_air_s("LONG_FAST", 50) == pytest.approx(0.64, abs=0.01)
    assert airtime.time_on_air_s("MEDIUM_FAST", 50) == pytest.approx(0.18, abs=0.01)


@pytest.mark.parametrize(("n", "i", "lf", "mf"), DOC_TABLE)
def test_utilization_reproduces_doc_table(n, i, lf, mf):
    assert round(airtime.utilization(n, i, "LONG_FAST") * 100) == lf
    assert round(airtime.utilization(n, i, "MEDIUM_FAST") * 100) == mf


def test_slower_preset_costs_more():
    toa = [
        airtime.time_on_air_s(p, 50)
        for p in ("SHORT_FAST", "MEDIUM_FAST", "LONG_FAST", "LONG_SLOW")
    ]
    assert toa == sorted(toa)


def test_max_nodes_and_status():
    n = airtime.max_nodes(60, "LONG_FAST")
    assert (
        airtime.utilization(n, 60, "LONG_FAST")
        <= 0.25
        < airtime.utilization(n + 1, 60, "LONG_FAST")
    )
    assert airtime.status(0.1) == "ok"
    assert airtime.status(0.3) == "delayed"
    assert airtime.status(0.5) == "throttled"
