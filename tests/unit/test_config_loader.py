import pytest
import yaml
from pydantic import SecretStr
from assertllm.config.loader import load_config, _resolve_env_vars
from assertllm.settings import settings


def test_resolve_env_var_from_settings_secret(monkeypatch):
    monkeypatch.setattr(settings, "groq_api_key", SecretStr("secret-value"))
    resolved = _resolve_env_vars("Bearer ${GROQ_API_KEY}")
    assert resolved == "Bearer secret-value"


def test_resolve_env_var_from_settings_plain_string(monkeypatch):
    monkeypatch.setattr(settings, "ollama_host", "http://custom-host:1234")
    resolved = _resolve_env_vars("${OLLAMA_HOST}/api")
    assert resolved == "http://custom-host:1234/api"


def test_resolve_env_var_falls_back_to_os_environ(monkeypatch):
    monkeypatch.setenv("MY_CUSTOM_TOKEN", "abc123")
    resolved = _resolve_env_vars("Bearer ${MY_CUSTOM_TOKEN}")
    assert resolved == "Bearer abc123"


def test_resolve_env_var_missing_raises():
    with pytest.raises(ValueError, match="MISSING_VAR_XYZ"):
        _resolve_env_vars("${MISSING_VAR_XYZ}")


def test_resolve_env_vars_walks_nested_dict_and_list(monkeypatch):
    monkeypatch.setenv("NESTED_VAR", "nested-value")
    data = {
        "headers": {"Authorization": "Bearer ${NESTED_VAR}"},
        "list_field": ["${NESTED_VAR}", "plain"],
    }
    resolved = _resolve_env_vars(data)
    assert resolved["headers"]["Authorization"] == "Bearer nested-value"
    assert resolved["list_field"][0] == "nested-value"
    assert resolved["list_field"][1] == "plain"


def test_resolve_env_vars_leaves_non_string_values_untouched():
    data = {"count": 5, "flag": True, "nothing": None}
    resolved = _resolve_env_vars(data)
    assert resolved == data


def test_load_config_valid_yaml_resolves_env_vars(tmp_path, monkeypatch):
    monkeypatch.setenv("MY_TOKEN", "tok-123")
    config_path = tmp_path / "sample.yaml"
    config_path.write_text(yaml.dump({
        "judge": {"provider": "ollama", "model": "llama3"},
        "tests": [
            {
                "name": "t1",
                "endpoint": "https://example.com/chat",
                "headers": {"Authorization": "Bearer ${MY_TOKEN}"},
                "body": {"message": "hi"},
                "assert": ["is polite"],
            }
        ],
    }))
    config = load_config(str(config_path))
    assert config.judge.provider == "ollama"
    assert config.tests[0].headers["Authorization"] == "Bearer tok-123"


def test_load_config_invalid_config_raises_friendly_error_with_test_name(tmp_path):
    config_path = tmp_path / "bad.yaml"
    config_path.write_text(yaml.dump({
        "judge": {"provider": "ollama", "model": "llama3"},
        "tests": [
            {
                "name": "broken test",
                "endpoint": "not-a-valid-url",
                "body": {"message": "hi"},
                "assert": ["is polite"],
            }
        ],
    }))
    with pytest.raises(ValueError, match="broken test"):
        load_config(str(config_path))


def test_load_config_missing_env_var_raises(tmp_path):
    config_path = tmp_path / "missing_var.yaml"
    config_path.write_text(yaml.dump({
        "judge": {"provider": "ollama", "model": "llama3"},
        "tests": [
            {
                "name": "t1",
                "endpoint": "https://example.com/chat",
                "headers": {"Authorization": "Bearer ${TOTALLY_UNSET_VAR}"},
                "body": {"message": "hi"},
                "assert": ["is polite"],
            }
        ],
    }))
    with pytest.raises(ValueError, match="TOTALLY_UNSET_VAR"):
        load_config(str(config_path))