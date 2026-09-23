from assertllm.judges.base import BaseJudge
from assertllm.judges.anthropic import AnthropicJudge
from assertllm.judges.groq import GroqJudge
from assertllm.judges.openai import OpenAIJudge
from assertllm.models.schema import JudgeConfig
from assertllm.settings import settings
from assertllm.constants.providers import SUPPORTED_PROVIDERS, PROVIDERS_REQUIRING_KEY


def get_judge(config: JudgeConfig) -> BaseJudge:
    provider = config.provider.lower()
    if provider == "anthropic":
        return AnthropicJudge(config.model, settings.anthropic_api_key)
    if provider == "groq":
        return GroqJudge(config.model, settings.groq_api_key)
    if provider == "openai":
        return OpenAIJudge(config.model, settings.openai_api_key)
    raise ValueError(f"Unsupported judge provider: '{provider}'")