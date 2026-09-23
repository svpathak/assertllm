import json
from typer.testing import CliRunner
from assertllm.cli import app
from assertllm.storage.runs import runs_dir_for_config

runner = CliRunner()


def _write_run(config_path, run_id, tests, timestamp="2026-01-01T00:00:00"):
    runs_dir = runs_dir_for_config(config_path)
    runs_dir.mkdir(parents=True, exist_ok=True)
    record = {
        "run_id": run_id,
        "config": config_path,
        "timestamp": timestamp,
        "tests": tests
    }
    (runs_dir / f"{run_id}.json").write_text(json.dumps(record))


def _test(name, passed, is_error=False, error=None):
    if is_error:
        return {"name": name, "is_error": True, "error": error, "assertions": None}
    return {
        "name": name,
        "is_error": False,
        "error": None,
        "assertions": [{"assertion": "is polite", "passed": passed}]
    }


def test_head_without_base_errors(isolated_cwd):
    result = runner.invoke(app, ["diff", "--config", "sample.yaml", "--head", "-1"])
    assert result.exit_code == 1
    assert "--head cannot be used without --base" in result.output


def test_no_runs_found_errors(isolated_cwd):
    result = runner.invoke(app, ["diff", "--config", "sample.yaml"])
    assert result.exit_code == 1
    assert "No runs found" in result.output


def test_only_one_run_errors(isolated_cwd):
    _write_run("sample.yaml", 1, [_test("t1", True)])
    result = runner.invoke(app, ["diff", "--config", "sample.yaml"])
    assert result.exit_code == 1
    assert "Need at least 2 runs" in result.output


def test_base_and_head_same_run_errors(isolated_cwd):
    _write_run("sample.yaml", 1, [_test("t1", True)])
    _write_run("sample.yaml", 2, [_test("t1", True)])
    result = runner.invoke(app, ["diff", "--config", "sample.yaml", "--base", "1", "--head", "1"])
    assert result.exit_code == 1
    assert "resolve to the same run" in result.output


def test_no_drift_exits_zero(isolated_cwd):
    _write_run("sample.yaml", 1, [_test("t1", True)])
    _write_run("sample.yaml", 2, [_test("t1", True)])
    result = runner.invoke(app, ["diff", "--config", "sample.yaml"])
    assert result.exit_code == 0
    assert "OK" in result.output
    assert "t1" in result.output


def test_drift_exits_one_and_shows_flip(isolated_cwd):
    _write_run("sample.yaml", 1, [_test("t1", True)])
    _write_run("sample.yaml", 2, [_test("t1", False)])
    result = runner.invoke(app, ["diff", "--config", "sample.yaml"])
    assert result.exit_code == 1
    assert "DRIFT" in result.output
    assert "PASS -> FAIL" in result.output


def test_new_test_shown_as_new(isolated_cwd):
    _write_run("sample.yaml", 1, [_test("t1", True)])
    _write_run("sample.yaml", 2, [_test("t1", True), _test("t2", True)])
    result = runner.invoke(app, ["diff", "--config", "sample.yaml"])
    assert "NEW" in result.output
    assert "t2" in result.output


def test_removed_test_shown_as_gone(isolated_cwd):
    _write_run("sample.yaml", 1, [_test("t1", True), _test("t2", True)])
    _write_run("sample.yaml", 2, [_test("t1", True)])
    result = runner.invoke(app, ["diff", "--config", "sample.yaml"])
    assert "GONE" in result.output
    assert "t2" in result.output


def test_error_test_is_skipped_not_treated_as_drift(isolated_cwd):
    _write_run("sample.yaml", 1, [_test("t1", True)])
    _write_run("sample.yaml", 2, [_test("t1", None, is_error=True, error="timeout")])
    result = runner.invoke(app, ["diff", "--config", "sample.yaml"])
    assert result.exit_code == 0
    assert "SKIP" in result.output


def test_explicit_base_and_head(isolated_cwd):
    _write_run("sample.yaml", 1, [_test("t1", True)])
    _write_run("sample.yaml", 2, [_test("t1", False)])
    _write_run("sample.yaml", 3, [_test("t1", True)])
    result = runner.invoke(app, ["diff", "--config", "sample.yaml", "--base", "1", "--head", "3"])
    assert result.exit_code == 0
    assert "OK" in result.output