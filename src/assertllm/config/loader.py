import re
import yaml
from assertllm.models.schema import Config
from assertllm.settings import settings


def _resolve_env_vars(value: object) -> object:
    if isinstance(value, str):
        def replacer(match: re.Match) -> str:
            var_name = match.group(1).lower()
            resolved = getattr(settings, var_name, None)
            if resolved is None:
                raise ValueError(f"Environment variable '{match.group(1)}' is not set")
            return resolved.get_secret_value() if hasattr(resolved, "get_secret_value") else str(resolved)
        return re.sub(r"\$\{(\w+)\}", replacer, value)
    if isinstance(value, dict):
        return {k: _resolve_env_vars(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_resolve_env_vars(i) for i in value]
    return value


def load_config(path: str) -> Config:
    with open(path, "r") as f:
        raw = yaml.safe_load(f)
    resolved = _resolve_env_vars(raw)
    return Config.model_validate(resolved)