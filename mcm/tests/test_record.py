import io

import pytest

from mcm.contract.record import (
    RECORD_SCHEMA,
    PacketHeader,
    PositionFix,
    RadioRecord,
    read_jsonl,
    write_jsonl,
)


def _rec(seq=1, **kw):
    return RadioRecord(
        seq=seq,
        rx_time_host="2026-10-03T14:00:01.000000Z",
        header=PacketHeader(from_node=10, hop_start=3, hop_limit=kw.pop("hop_limit", 3)),
        portnum="POSITION_APP",
        kind="position",
        position=PositionFix(lat=39.99, lon=-105.28, device_time="2026-10-03T14:00:00Z"),
        **kw,
    )


def test_json_round_trip():
    r = _rec()
    assert RadioRecord.from_json(r.to_json()) == r
    assert r.to_dict()["schema"] == RECORD_SCHEMA


def test_every_header_field_present_even_when_empty():
    d = _rec().to_dict()["header"]
    for key in (
        "from_node",
        "to_node",
        "mesh_id",
        "hop_start",
        "hop_limit",
        "relay_node",
        "rx_snr",
        "rx_rssi",
    ):
        assert key in d


def test_hops_and_direct():
    assert _rec().header.hops_taken == 0
    assert _rec().header.heard_directly is True
    relayed = _rec(hop_limit=1).header
    assert relayed.hops_taken == 2 and relayed.heard_directly is False
    assert PacketHeader(from_node=1).heard_directly is None


def test_unknown_kind_rejected():
    with pytest.raises(ValueError):
        RadioRecord(seq=1, rx_time_host="x", header=PacketHeader(1), portnum="X", kind="nope")


def test_other_schema_rejected():
    d = _rec().to_dict()
    d["schema"] = "mcm.radio_record/9"
    with pytest.raises(ValueError):
        RadioRecord.from_dict(d)


def test_jsonl(tmp_path):
    buf = io.StringIO()
    assert write_jsonl([_rec(1), _rec(2)], buf) == 2
    p = tmp_path / "feed.jsonl"
    p.write_text(buf.getvalue() + "\n", encoding="utf-8")
    assert [r.seq for r in read_jsonl(p)] == [1, 2]
