from assertllm.judges.base import BaseJudge
from assertllm.judges.anthropic import AnthropicJudge
from assertllm.judges.groq import GroqJudge
from assertllm.models.schema import JudgeConfig


def get_judge(config: JudgeConfig) -> BaseJudge:
    provider = config.provider.lower()
    if provider == "anthropic":
        return AnthropicJudge(config)
    if provider == "groq":
        return GroqJudge(config)
    raise ValueError(f"Unsupported judge provider: '{provider}'")