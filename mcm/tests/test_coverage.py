from mcm.contract.record import PacketHeader, PositionFix, RadioRecord
from mcm.coverage.model import FreeSpaceModel, RadioParams, Site, distance_m, free_space_loss_db
from mcm.coverage.validate import agreement, compare, direct_positions

GW = Site(39.9936, -105.2811, antenna_agl_m=3)


def test_distance_one_degree_latitude():
    assert abs(distance_m(Site(0, 0), Site(1, 0)) - 111_195) < 50


def test_free_space_loss_grows_6db_per_doubling():
    assert abs(free_space_loss_db(2000, 915) - free_space_loss_db(1000, 915) - 6.02) < 0.01


def test_classes_move_from_covered_to_shadow_with_distance():
    radio = RadioParams(sensitivity_dbm=-100.0)
    far = [Site(39.9936 + k * 0.1, -105.2811) for k in (0.01, 1, 10)]
    classes = [lk.link_class for lk in FreeSpaceModel().predict(GW, far, radio)]
    assert classes[0] == "covered" and classes[-1] == "shadow"


def _pos(seq, lat, hop_limit):
    return RadioRecord(
        seq=seq,
        rx_time_host="T",
        portnum="POSITION_APP",
        kind="position",
        header=PacketHeader(from_node=5, hop_start=3, hop_limit=hop_limit, rx_rssi=-100),
        position=PositionFix(lat, -105.2811),
    )


def test_only_direct_packets_are_compared():
    recs = [_pos(1, 40.0, 3), _pos(2, 40.0, 1)]
    assert [r.seq for r in direct_positions(recs)] == [1]
    comps = compare(recs, GW, FreeSpaceModel(), RadioParams())
    assert len(comps) == 1 and agreement(comps) == 1.0
    assert agreement([]) is None
