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


def _passing_test(name="t1"):
    return {
        "name": name,
        "is_error": False,
        "error": None,
        "status_code": 200,
        "input": {"message": "hi"},
        "response": "hello there",
        "duration_ms": 120,
        "assertions": [{"assertion": "is polite", "passed": True}]
    }


def _failing_test(name="t2"):
    return {
        "name": name,
        "is_error": False,
        "error": None,
        "status_code": 200,
        "input": {"message": "hi"},
        "response": "hello there",
        "duration_ms": 120,
        "assertions": [{"assertion": "is polite", "passed": False}]
    }


def _error_test(name="t3"):
    return {
        "name": name,
        "is_error": True,
        "error": "connection refused",
        "status_code": None,
        "input": {"message": "hi"},
        "response": None,
        "duration_ms": 50,
        "assertions": None
    }


def test_list_and_run_together_errors(isolated_cwd):
    result = runner.invoke(app, ["inspect", "--config", "sample.yaml", "--list", "--run", "1"])
    assert result.exit_code == 1
    assert "cannot be used together" in result.output


def test_list_and_test_together_errors(isolated_cwd):
    result = runner.invoke(app, ["inspect", "--config", "sample.yaml", "--list", "--test", "t1"])
    assert result.exit_code == 1
    assert "cannot be used together" in result.output


def test_list_with_no_runs(isolated_cwd):
    result = runner.invoke(app, ["inspect", "--config", "sample.yaml", "--list"])
    assert result.exit_code == 0
    assert "No runs found" in result.output


def test_list_shows_all_runs_newest_first(isolated_cwd):
    _write_run("sample.yaml", 1, [_passing_test()])
    _write_run("sample.yaml", 2, [_failing_test()])
    result = runner.invoke(app, ["inspect", "--config", "sample.yaml", "--list"])
    assert result.exit_code == 0
    idx1 = result.output.index("#1")
    idx2 = result.output.index("#2")
    assert idx2 < idx1


def test_run_not_found_errors(isolated_cwd):
    _write_run("sample.yaml", 1, [_passing_test()])
    result = runner.invoke(app, ["inspect", "--config", "sample.yaml", "--run", "99"])
    assert result.exit_code == 1
    assert "No run #99 found" in result.output


def test_default_shows_latest_run(isolated_cwd):
    _write_run("sample.yaml", 1, [_passing_test("old")])
    _write_run("sample.yaml", 2, [_passing_test("new")])
    result = runner.invoke(app, ["inspect", "--config", "sample.yaml"])
    assert result.exit_code == 0
    assert "#2" in result.output
    assert "new" in result.output
    assert "old" not in result.output


def test_shows_pass_and_fail_for_each_test(isolated_cwd):
    _write_run("sample.yaml", 1, [_passing_test("t1"), _failing_test("t2")])
    result = runner.invoke(app, ["inspect", "--config", "sample.yaml", "--run", "1"])
    assert result.exit_code == 0
    assert "PASS" in result.output
    assert "t1" in result.output
    assert "FAIL" in result.output
    assert "t2" in result.output


def test_shows_error_test_with_error_message(isolated_cwd):
    _write_run("sample.yaml", 1, [_error_test("t3")])
    result = runner.invoke(app, ["inspect", "--config", "sample.yaml", "--run", "1"])
    assert result.exit_code == 0
    assert "ERROR" in result.output
    assert "connection refused" in result.output


def test_test_filter_no_match_errors(isolated_cwd):
    _write_run("sample.yaml", 1, [_passing_test("t1")])
    result = runner.invoke(app, ["inspect", "--config", "sample.yaml", "--run", "1", "--test", "nonexistent"])
    assert result.exit_code == 1
    assert "No test named" in result.output


def test_test_filter_shows_only_matching_test(isolated_cwd):
    _write_run("sample.yaml", 1, [_passing_test("t1"), _failing_test("t2")])
    result = runner.invoke(app, ["inspect", "--config", "sample.yaml", "--run", "1", "--test", "t1"])
    assert result.exit_code == 0
    assert "t1" in result.output
    assert "t2" not in result.output