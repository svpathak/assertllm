from pydantic import BaseModel, ConfigDict, Field, field_validator, AnyHttpUrl
from assertllm.constants.http import ALLOWED_METHODS, DEFAULT_METHOD

class JudgeConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider: str
    model: str

    @field_validator("provider")
    @classmethod
    def provider_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("provider cannot be empty")
        return v.lower()

    @field_validator("model")
    @classmethod
    def model_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("model cannot be empty")
        return v


class TestConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    name: str
    endpoint: AnyHttpUrl
    method: str = DEFAULT_METHOD
    headers: dict[str, str] = {}
    body: dict
    assertions: list[str] = Field(alias="assert")

    @field_validator("method")
    @classmethod
    def method_must_be_valid(cls, v: str) -> str:
        upper = v.upper()
        if upper not in ALLOWED_METHODS:
            raise ValueError(f"method '{v}' is not valid. Must be one of: {', '.join(sorted(ALLOWED_METHODS))}")
        return upper

    @field_validator("body")
    @classmethod
    def body_not_empty(cls, v: dict) -> dict:
        if not v:
            raise ValueError("body cannot be empty")
        return v

    @field_validator("assertions", mode="before")
    @classmethod
    def assertions_not_empty(cls, v: list) -> list:
        if not v:
            raise ValueError("assert list cannot be empty")
        for i, item in enumerate(v):
            if not isinstance(item, str) or not item.strip():
                raise ValueError(f"assertion at index {i} is empty or not a string")
        return v

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("name cannot be empty")
        return v


class Config(BaseModel):
    model_config = ConfigDict(extra="forbid")

    judge: JudgeConfig
    tests: list[TestConfig]