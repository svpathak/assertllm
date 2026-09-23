from assertllm.models.schema import Config
from assertllm.settings import settings
from assertllm.constants.providers import PROVIDERS, SUPPORTED_PROVIDERS, PROVIDERS_REQUIRING_KEY


def validate_config(config: Config) -> None:
    provider = config.judge.provider.lower()

    if provider not in SUPPORTED_PROVIDERS:
        raise ValueError(
            f"Unsupported judge provider: '{provider}'. "
            f"Must be one of: {', '.join(sorted(SUPPORTED_PROVIDERS))}"
        )

    if provider in PROVIDERS_REQUIRING_KEY:
        attr = PROVIDERS[provider]["settings_attr"]
        if getattr(settings, attr) is None:
            raise ValueError(f"{attr.upper()} is not set in .env")

    if not config.tests:
        raise ValueError("Config must define at least one test")

    for test in config.tests:
        if not test.assertions:
            raise ValueError(f"Test '{test.name}' has no assertions defined")