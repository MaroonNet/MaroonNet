from mcm.radio.normalize import epoch_to_iso, normalize


def test_direct_position(lib_packets):
    r = normalize(lib_packets["position_direct"], seq=1, rx_time_host="T")
    assert r.kind == "position" and r.portnum == "POSITION_APP"
    assert abs(r.position.lat - 39.9936) < 1e-9 and abs(r.position.lon + 105.2811) < 1e-9
    assert r.position.alt_m == 1702.0
    assert r.position.device_time == "2026-10-03T13:59:58Z"
    assert r.position.precision_bits == 32 and r.position.pdop == 1.45
    h = r.header
    assert (h.from_node, h.mesh_id, h.rx_snr, h.rx_rssi) == (167772161, 1001, 6.25, -88)
    assert h.heard_directly
    assert r.rx_time_radio == "2026-10-03T14:00:00Z"
    assert r.decoded_extra == {"bitfield": 1}


def test_no_fix_is_none_not_zero(lib_packets):
    r = normalize(lib_packets["position_relayed_no_fix"], seq=2, rx_time_host="T")
    assert r.position.device_time is None
    assert r.rx_time_radio is None
    assert r.position.alt_m is None
    assert r.header.hops_taken == 2 and r.header.relay_node == 3
    assert r.position.precision_bits == 13  # reduced precision kept as reported


def test_telemetry(lib_packets):
    t = normalize(lib_packets["telemetry"], seq=3, rx_time_host="T").telemetry
    assert (t.battery_pct, t.voltage, t.channel_util, t.air_util_tx) == (87, 4.02, 18.4, 1.7)
    assert t.uptime_s == 5400 and t.device_time == "2026-10-03T14:00:10Z"


def test_text_and_node_info(lib_packets):
    assert normalize(lib_packets["text"], seq=4, rx_time_host="T").text == "Clue at trail junction"
    n = normalize(lib_packets["node_info"], seq=5, rx_time_host="T").node_info
    assert (n.node_id, n.short_name, n.hw_model) == ("!0a000003", "T2A", "HELTEC_V3")


def test_undecoded_still_a_record(lib_packets):
    r = normalize(lib_packets["undecoded"], seq=6, rx_time_host="T")
    assert r.kind == "undecoded" and r.portnum == "UNKNOWN"
    assert r.header.rx_rssi == -110  # signal data kept even when the payload is unreadable


def test_other_port_kept_in_extra(lib_packets):
    r = normalize(lib_packets["other_port"], seq=7, rx_time_host="T")
    assert r.kind == "other" and r.decoded_extra["routing"] == {"errorReason": "NONE"}


def test_bytes_become_base64():
    pkt = {"from": 1, "decoded": {"portnum": "PRIVATE_APP", "payload": b"\x01\x02"}}
    r = normalize(pkt, seq=1, rx_time_host="T")
    assert r.decoded_extra["payload"] == {"b64": "AQI="}
    r.to_json()  # JSON-safe


def test_epoch_zero_is_none():
    assert epoch_to_iso(0) is None and epoch_to_iso(None) is None
