import pytest
from pydantic import SecretStr
from assertllm.config.validator import validate_config
from assertllm.models.schema import Config, JudgeConfig, TestConfig
from assertllm.settings import settings


def _test_config(**overrides):
    kwargs = {
        "name": "sample",
        "endpoint": "https://example.com/chat",
        "body": {"message": "hi"},
        "assert": ["is polite"]
    }
    kwargs.update(overrides)
    return TestConfig(**kwargs)


def test_unsupported_provider_raises():
    config = Config(
        judge=JudgeConfig(provider="bogus", model="x"),
        tests=[_test_config()]
    )
    with pytest.raises(ValueError, match="Unsupported judge provider"):
        validate_config(config)


def test_provider_requires_key_but_missing_raises(monkeypatch):
    monkeypatch.setattr(settings, "groq_api_key", None)
    config = Config(
        judge=JudgeConfig(provider="groq", model="llama-3.3-70b-versatile"),
        tests=[_test_config()]
    )
    with pytest.raises(ValueError, match="GROQ_API_KEY is not set"):
        validate_config(config)


def test_provider_requires_key_and_present_passes(monkeypatch):
    monkeypatch.setattr(settings, "groq_api_key", SecretStr("test-key"))
    config = Config(
        judge=JudgeConfig(provider="groq", model="llama-3.3-70b-versatile"),
        tests=[_test_config()]
    )
    validate_config(config)


def test_empty_tests_list_raises(monkeypatch):
    monkeypatch.setattr(settings, "groq_api_key", SecretStr("test-key"))
    config = Config(
        judge=JudgeConfig(provider="groq", model="llama-3.3-70b-versatile"),
        tests=[]
    )
    with pytest.raises(ValueError, match="at least one test"):
        validate_config(config)


def test_test_with_no_assertions_raises(monkeypatch):
    monkeypatch.setattr(settings, "groq_api_key", SecretStr("test-key"))
    # TestConfig's own validator blocks empty assertions on normal construction,
    # so model_construct is used here to exercise the validator-layer check directly.
    broken = TestConfig.model_construct(
        name="broken",
        endpoint="https://example.com/chat",
        method="POST",
        headers={},
        body={"message": "hi"},
        assertions=[],
        expected_status=None
    )
    config = Config(
        judge=JudgeConfig(provider="groq", model="llama-3.3-70b-versatile"),
        tests=[broken]
    )
    with pytest.raises(ValueError, match="has no assertions"):
        validate_config(config)