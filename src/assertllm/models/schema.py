from pydantic import BaseModel, Field, SecretStr

class JudgeConfig(BaseModel):
    provider: str
    model: str

class TestConfig(BaseModel):
    name: str
    endpoint: str
    method: str = "POST"
    headers: dict = {}
    body: dict
    assertions: list[str] = Field(alias="assert")

    model_config = {"populate_by_name": True}

class Config(BaseModel):
    judge: JudgeConfig
    tests: list[TestConfig]