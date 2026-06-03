import re
import yaml
from pydantic import ValidationError
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


def _build_test_labels(raw: dict) -> dict[int, str]:
    labels = {}
    if not isinstance(raw, dict):
        return labels
    tests = raw.get("tests", [])
    if not isinstance(tests, list):
        return labels
    for i, test in enumerate(tests):
        name = test.get("name") if isinstance(test, dict) else None
        labels[i] = f"'{name}'" if name else f"test {i + 1}"
    return labels


def _format_validation_error(e: ValidationError, test_labels: dict[int, str]) -> str:
    errors = []
    for err in e.errors():
        loc = list(err["loc"])

        if len(loc) >= 2 and loc[0] == "tests" and isinstance(loc[1], int):
            index = loc[1]
            label = test_labels.get(index, f"test {index + 1}")
            loc = [f"test {label}"] + loc[2:]

        location = " -> ".join(str(part) for part in loc)
        msg = err["msg"].replace("Value error, ", "")
        errors.append(f"  {location}: {msg}")

    return "Invalid config:\n" + "\n".join(errors)


def load_config(path: str) -> Config:
    with open(path, "r") as f:
        raw = yaml.safe_load(f)
    resolved = _resolve_env_vars(raw)
    test_labels = _build_test_labels(raw)
    try:
        return Config.model_validate(resolved)
    except ValidationError as e:
        raise ValueError(_format_validation_error(e, test_labels)) from None