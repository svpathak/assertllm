import yaml
from unittest.mock import patch
from pydantic import SecretStr
from typer.testing import CliRunner
from assertllm.cli import app
from assertllm.models.results import AssertionResult, TestResult
from assertllm.settings import settings

runner = CliRunner()


def _write_config(path, **overrides):
    data = {
        "judge": {"provider": "groq", "model": "llama-3.3-70b-versatile"},
        "tests": [
            {
                "name": "t1",
                "endpoint": "https://example.com/chat",
                "body": {"message": "hi"},
                "assert": ["is polite"]
            }
        ]
    }
    data.update(overrides)
    path.write_text(yaml.dump(data))
    return path


def test_run_command_missing_file_shows_friendly_error(isolated_cwd):
    result = runner.invoke(app, ["run", "does_not_exist.yaml"])
    assert result.exit_code == 1
    assert "Error" in result.stdout or "Error" in result.output


def test_run_command_invalid_provider_shows_friendly_error(isolated_cwd):
    config_path = isolated_cwd / "bad.yaml"
    _write_config(config_path, judge={"provider": "bogus", "model": "x"})
    result = runner.invoke(app, ["run", str(config_path)])
    assert result.exit_code == 1
    assert "Unsupported judge provider" in result.output


def test_run_command_missing_api_key_shows_friendly_error(isolated_cwd, monkeypatch):
    monkeypatch.setattr(settings, "groq_api_key", None)
    config_path = isolated_cwd / "sample.yaml"
    _write_config(config_path)
    result = runner.invoke(app, ["run", str(config_path)])
    assert result.exit_code == 1
    assert "GROQ_API_KEY is not set" in result.output


def test_run_command_test_filter_not_found(isolated_cwd, monkeypatch):
    monkeypatch.setattr(settings, "groq_api_key", SecretStr("test-key"))
    config_path = isolated_cwd / "sample.yaml"
    _write_config(config_path)
    result = runner.invoke(app, ["run", str(config_path), "--test", "nonexistent"])
    assert result.exit_code == 1
    assert "No test named" in result.output


def test_run_command_success_all_pass_exits_zero(isolated_cwd, monkeypatch):
    monkeypatch.setattr(settings, "groq_api_key", SecretStr("test-key"))
    config_path = isolated_cwd / "sample.yaml"
    _write_config(config_path)

    fake_result = TestResult(
        name="t1",
        input={"message": "hi"},
        response="hello",
        assertion_results=[AssertionResult(assertion="is polite", passed=True)]
    )
    with patch("assertllm.cli.commands.run.run", return_value=([fake_result], isolated_cwd / "1.json", 1)):
        result = runner.invoke(app, ["run", str(config_path)])

    assert result.exit_code == 0
    assert "Run #1 saved" in result.output


def test_run_command_any_failure_exits_one(isolated_cwd, monkeypatch):
    monkeypatch.setattr(settings, "groq_api_key", SecretStr("test-key"))
    config_path = isolated_cwd / "sample.yaml"
    _write_config(config_path)

    fake_result = TestResult(
        name="t1",
        input={"message": "hi"},
        response="hello",
        assertion_results=[AssertionResult(assertion="is polite", passed=False)]
    )
    with patch("assertllm.cli.commands.run.run", return_value=([fake_result], isolated_cwd / "1.json", 1)):
        result = runner.invoke(app, ["run", str(config_path)])

    assert result.exit_code == 1