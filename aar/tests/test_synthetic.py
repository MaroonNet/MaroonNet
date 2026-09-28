"""The synthetic mission is deterministic, complete, and exercises gaps and no-fix reports."""

from aar.cli import main
from aar.replay import gaps, state_at
from aar.store import connect, create
from aar.synthetic import generate


def test_generate_is_deterministic_and_complete(tmp_path):
    a = create(tmp_path / "a.sqlite", "a", "a", "2026-10-03T14:00:00Z")
    b = create(tmp_path / "b.sqlite", "b", "b", "2026-10-03T14:00:00Z")
    sa = generate(a, n_nodes=6, hours=3, interval_s=60, seed=3)
    sb = generate(b, n_nodes=6, hours=3, interval_s=60, seed=3)
    assert sa == sb
    assert sa.nodes == 6 and sa.positions > 0 and sa.events >= 6

    # Every typed row has its packet row; every position belongs to a known node.
    orphan = a.execute(
        "SELECT count(*) FROM position p LEFT JOIN packet k USING (packet_id)"
        " WHERE k.packet_id IS NULL"
    ).fetchone()[0]
    unknown = a.execute(
        "SELECT count(*) FROM position WHERE node_num NOT IN (SELECT node_num FROM node)"
    ).fetchone()[0]
    assert orphan == 0 and unknown == 0
    assert a.execute("SELECT ended_at FROM mission").fetchone()[0] == sa.ended_at


def test_generate_produces_gaps_and_no_fix_reports(tmp_path):
    con = create(tmp_path / "m.sqlite", "m", "m", "2026-10-03T14:00:00Z")
    s = generate(con, n_nodes=10, hours=6, interval_s=60, seed=7)
    assert s.positions_without_fix > 0
    assert len(gaps(con, threshold_s=300)) > 0
    assert len(state_at(con, "2026-10-03T17:00:00Z")) == 10  # everyone has reported by then


def test_cli_synth_then_summary(tmp_path, capsys):
    out = tmp_path / "synthetic" / "m.sqlite"
    assert main(["synth", "--out", str(out), "--nodes", "3", "--hours", "1", "--seed", "1"]) == 0
    assert main(["summary", str(out)]) == 0
    text = capsys.readouterr().out
    assert "wrote" in text and "nodes     3" in text
    connect(out).close()
