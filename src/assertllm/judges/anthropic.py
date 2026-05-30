import anthropic
from assertllm.judges.base import BaseJudge
from assertllm.judges.utils import JudgeUtils
from assertllm.models.schema import JudgeConfig


class AnthropicJudge(BaseJudge):
    def __init__(self, config: JudgeConfig) -> None:
        api_key = config.api_key.get_secret_value() if config.api_key else None
        self._client = anthropic.Anthropic(api_key=api_key)
        self._model = config.model

    def evaluate(self, response: str, assertions: list[str]) -> list[bool]:
        prompt = JudgeUtils.build_prompt(response, assertions)
        message = self._client.messages.create(
            model=self._model,
            max_tokens=256,
            messages=[{"role": "user", "content": prompt}],
        )
        return JudgeUtils.parse_response(message.content[0].text, len(assertions))