PROVIDERS: dict[str, dict] = {
    "anthropic": {"requires_key": True, "settings_attr": "anthropic_api_key"},
    "groq":      {"requires_key": True, "settings_attr": "groq_api_key"},
    "openai":    {"requires_key": True, "settings_attr": "openai_api_key"},
    "ollama":    {"requires_key": False, "settings_attr": None},
}

SUPPORTED_PROVIDERS: set[str] = set(PROVIDERS)
PROVIDERS_REQUIRING_KEY: set[str] = {p for p, v in PROVIDERS.items() if v["requires_key"]}