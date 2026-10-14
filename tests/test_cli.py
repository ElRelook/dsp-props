import json
import pathlib

from dsp_props.cli import discover, main

EXAMPLE = str(pathlib.Path(__file__).resolve().parents[1] / "examples" / "filters.py")


def test_discover_finds_declared_operators_in_a_file():
    names = [n.split(":")[1] for n, _ in discover(EXAMPLE)]
    assert names == ["buggy_fft", "fft", "lowpass", "resample_2_3"]


def test_discover_reads_registries_and_single_attributes():
    found = discover("mutants.multirate_mutants")
    assert any("MUTANTS['rate_floor_length']" in n for n, _ in found)
    assert len(discover("mutants.multirate_mutants:REFERENCE")) == 1


def test_check_exit_status_and_json(tmp_path, capsys):
    out = tmp_path / "r.json"
    assert main(["check", f"{EXAMPLE}:fft", "--examples", "20", "--json", str(out)]) == 0
    assert json.loads(out.read_text())["operators"][0]["ok"] is True
    md = tmp_path / "r.md"
    assert main(["check", f"{EXAMPLE}:buggy_fft", "--examples", "20", "--markdown", str(md)]) == 1
    assert "**FAIL**" in md.read_text()
    assert "minimal input" in capsys.readouterr().out


def test_unknown_module_is_a_usage_error():
    assert main(["check", "no_such_module_xyz"]) == 2
