import pytest
from pydantic import SecretStr
from assertllm.judges import get_judge
from assertllm.judges.anthropic import AnthropicJudge
from assertllm.judges.groq import GroqJudge
from assertllm.judges.openai import OpenAIJudge
from assertllm.models.schema import JudgeConfig
from assertllm.settings import settings


def test_get_judge_returns_anthropic_judge():
    config = JudgeConfig(provider="anthropic", model="claude-haiku-4-5")
    judge = get_judge(config)
    assert isinstance(judge, AnthropicJudge)


def test_get_judge_returns_groq_judge(monkeypatch):
    monkeypatch.setattr(settings, "groq_api_key", SecretStr("test-key"))
    config = JudgeConfig(provider="groq", model="llama-3.3-70b-versatile")
    judge = get_judge(config)
    assert isinstance(judge, GroqJudge)


def test_get_judge_returns_openai_judge(monkeypatch):
    monkeypatch.setattr(settings, "openai_api_key", SecretStr("test-key"))
    config = JudgeConfig(provider="openai", model="gpt-4o")
    judge = get_judge(config)
    assert isinstance(judge, OpenAIJudge)


def test_get_judge_is_case_insensitive_on_provider():
    config = JudgeConfig(provider="Anthropic", model="claude-haiku-4-5")
    judge = get_judge(config)
    assert isinstance(judge, AnthropicJudge)


def test_get_judge_unsupported_provider_raises():
    config = JudgeConfig(provider="ollama", model="llama3")
    with pytest.raises(ValueError, match="Unsupported judge provider: 'ollama'"):
        get_judge(config)