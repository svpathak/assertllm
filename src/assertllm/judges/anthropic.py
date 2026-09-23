from anthropic import Anthropic
from pydantic import SecretStr
from assertllm.judges.base import BaseJudge
from assertllm.judges.utils import JudgeUtils


class AnthropicJudge(BaseJudge):
    def __init__(self, model: str, api_key: SecretStr | None) -> None:
        self._client = Anthropic(api_key=api_key.get_secret_value() if api_key else None)
        self._model = model

    def evaluate(self, response: str, assertions: list[str]) -> list[bool]:
        prompt = JudgeUtils.build_prompt(response, assertions)
        message = self._client.messages.create(
            model=self._model,
            max_tokens=256,
            messages=[{"role": "user", "content": prompt}],
        )
        return JudgeUtils.parse_response(message.content[0].text, len(assertions))