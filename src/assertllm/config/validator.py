from assertllm.models.schema import Config

PROVIDER_REQUIRED_KEYS = {
    "anthropic": "anthropic_api_key",
    "openai": "openai_api_key",
    "groq": "groq_api_key",
}


def validate_config(config: Config) -> None:
    provider = config.judge.provider.lower()

    if provider not in (*PROVIDER_REQUIRED_KEYS, "ollama"):
        raise ValueError(f"Unsupported judge provider: '{provider}'")

    if provider in PROVIDER_REQUIRED_KEYS and config.judge.api_key is None:
        field = PROVIDER_REQUIRED_KEYS[provider]
        raise ValueError(f"Judge provider '{provider}' requires api_key (or set {field.upper()} in .env)")

    if not config.tests:
        raise ValueError("Config must define at least one test")

    for test in config.tests:
        if not test.assertions:
            raise ValueError(f"Test '{test.name}' has no assertions defined")