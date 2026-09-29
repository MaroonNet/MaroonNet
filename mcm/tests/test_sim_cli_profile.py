from mcm import cli
from mcm.contract.record import RadioRecord, read_jsonl
from mcm.radio import profile
from mcm.radio.gateway import Gateway
from mcm.sim import synthetic


def test_synthetic_is_deterministic_and_realistic():
    a = [r.to_json() for r in synthetic.records(n_nodes=4, hours=1, seed=3)]
    b = [r.to_json() for r in synthetic.records(n_nodes=4, hours=1, seed=3)]
    assert a == b
    recs = [RadioRecord.from_json(x) for x in a]
    assert [r.seq for r in recs] == list(range(1, len(recs) + 1))
    kinds = {r.kind for r in recs}
    assert {"position", "telemetry"} <= kinds
    assert any(not r.header.heard_directly for r in recs)


def test_profile_loads_and_is_not_pinned_yet():
    p = profile.load()
    assert p.transport == "serial"
    assert p.is_pinned is False  # the pin is Open; this test changes the day it is recorded
    assert p.gap_threshold_s == p.gap_factor * p.broadcast_interval_s
    assert "not pinned" in profile.check_firmware(p, "2.0.0")


def test_gateway_numbers_and_hands_off_without_a_radio(lib_packets):
    got = []
    gw = Gateway(on_record=got.append)
    gw.handle_packet(lib_packets["position_direct"])
    gw.handle_packet(lib_packets["undecoded"])
    assert [r.seq for r in got] == [1, 2]
    assert got[1].kind == "undecoded"


def test_gateway_survives_a_failing_handler(lib_packets):
    def boom(_):
        raise RuntimeError("daemon bug")

    rec = Gateway(on_record=boom).handle_packet(lib_packets["telemetry"])
    assert rec.seq == 1


def test_cli_synth_then_inspect(tmp_path, capsys):
    out = tmp_path / "feed.jsonl"
    assert cli.main(["synth", "--out", str(out), "--nodes", "3", "--hours", "2"]) == 0
    assert cli.main(["synth", "--out", str(out)]) == 1  # never overwrites
    assert len(list(read_jsonl(out))) > 0
    assert cli.main(["inspect", str(out)]) == 0
    assert "records from 3 radios" in capsys.readouterr().out


def test_cli_airtime_and_profile(capsys):
    assert cli.main(["airtime", "--nodes", "10", "--interval", "60"]) == 0
    assert cli.main(["profile"]) == 0
    assert "32.1%" in capsys.readouterr().out
