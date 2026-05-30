from groq import Groq
from assertllm.judges.base import BaseJudge
from assertllm.judges.utils import JudgeUtils
from assertllm.models.schema import JudgeConfig


class GroqJudge(BaseJudge):
    def __init__(self, config: JudgeConfig) -> None:
        api_key = config.api_key.get_secret_value() if config.api_key else None
        self._client = Groq(api_key=api_key)
        self._model = config.model

    def evaluate(self, response: str, assertions: list[str]) -> list[bool]:
        prompt = JudgeUtils.build_prompt(response, assertions)
        completion = self._client.chat.completions.create(
            model=self._model,
            max_tokens=256,
            messages=[{"role": "user", "content": prompt}]
        )
        return JudgeUtils.parse_response(completion.choices[0].message.content, len(assertions))