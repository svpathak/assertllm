from assertllm.models.schema import Config
from assertllm.settings import settings

PROVIDER_KEY_CHECK = {
    "anthropic": ("anthropic_api_key", "ANTHROPIC_API_KEY"),
    "openai": ("openai_api_key", "OPENAI_API_KEY"),
    "groq": ("groq_api_key", "GROQ_API_KEY"),
}


def validate_config(config: Config) -> None:
    provider = config.judge.provider.lower()

    if provider not in (*PROVIDER_KEY_CHECK, "ollama"):
        raise ValueError(f"Unsupported judge provider: '{provider}'")

    if provider in PROVIDER_KEY_CHECK:
        attr, env_var = PROVIDER_KEY_CHECK[provider]
        if getattr(settings, attr) is None:
            raise ValueError(f"Judge provider '{provider}' requires {env_var} to be set in .env")

    if not config.tests:
        raise ValueError("Config must define at least one test")

    for test in config.tests:
        if not test.assertions:
            raise ValueError(f"Test '{test.name}' has no assertions defined")