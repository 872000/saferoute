"""CLI validation: the --safety slider must stay in [0, 1].

main() guards this before dispatching to any command, so out-of-range
values fail fast with a usage error instead of reaching the router.
"""
import pytest

from saferoute.cli import main


@pytest.mark.parametrize("bad", ["-0.1", "1.5", "2"])
def test_safety_out_of_range_is_rejected(bad, capsys):
    with pytest.raises(SystemExit) as exc:
        main(["route", "--from", "A1", "--to", "T20", "--safety", bad])
    assert exc.value.code == 2  # argparse usage error
    assert "--safety must be in [0, 1]" in capsys.readouterr().err


@pytest.mark.parametrize("ok", ["0", "0.85", "1"])
def test_safety_boundaries_are_accepted(ok, capsys):
    # A valid route must run to completion instead of being rejected.
    # (cmd_route writes a map PNG into assets/; keep the demo seed fast.)
    rc = main(["route", "--from", "A1", "--to", "A2", "--safety", ok,
               "--seed", "42"])
    assert rc == 0
