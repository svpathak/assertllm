import pytest
from pydantic import ValidationError
from assertllm.models.schema import TestConfig, JudgeConfig, Config


def _base_test_kwargs(**overrides):
    kwargs = {
        "name": "sample test",
        "endpoint": "https://example.com/chat",
        "body": {"message": "hi"},
        "assert": ["response is polite"]
    }
    kwargs.update(overrides)
    return kwargs


def test_expected_status_defaults_to_none():
    t = TestConfig(**_base_test_kwargs())
    assert t.expected_status is None


@pytest.mark.parametrize("status", [100, 200, 401, 404, 500, 599])
def test_expected_status_accepts_valid_codes(status):
    t = TestConfig(**_base_test_kwargs(expected_status=status))
    assert t.expected_status == status


@pytest.mark.parametrize("status", [0, 99, 600, -1])
def test_expected_status_rejects_invalid_codes(status):
    with pytest.raises(ValidationError):
        TestConfig(**_base_test_kwargs(expected_status=status))


def test_extra_fields_forbidden_on_test_config():
    with pytest.raises(ValidationError):
        TestConfig(**_base_test_kwargs(unexpected_field="nope"))


def test_invalid_method_rejected():
    with pytest.raises(ValidationError):
        TestConfig(**_base_test_kwargs(method="FETCH"))


def test_method_uppercased():
    t = TestConfig(**_base_test_kwargs(method="post"))
    assert t.method == "POST"


def test_empty_body_rejected():
    with pytest.raises(ValidationError):
        TestConfig(**_base_test_kwargs(body={}))


def test_empty_assertions_rejected():
    with pytest.raises(ValidationError):
        TestConfig(**_base_test_kwargs(**{"assert": []}))


def test_empty_name_rejected():
    with pytest.raises(ValidationError):
        TestConfig(**_base_test_kwargs(name="   "))


def test_judge_config_provider_lowercased():
    j = JudgeConfig(provider="Groq", model="llama-3.3-70b-versatile")
    assert j.provider == "groq"


def test_judge_config_empty_provider_rejected():
    with pytest.raises(ValidationError):
        JudgeConfig(provider="  ", model="llama-3.3-70b-versatile")


def test_config_requires_at_least_one_test_field_but_not_enforced_here():
    # Config itself does not enforce non-empty tests list; that lives in the validator layer.
    c = Config(judge=JudgeConfig(provider="groq", model="llama-3.3-70b-versatile"), tests=[])
    assert c.tests == []