import hashlib
import json
import re
from pathlib import Path
from rich.console import Console

console = Console()

ASSERTLLM_DIR = ".assertllm"
RUNS_DIR = ".runs"


def config_to_folder(config_path: str) -> str:
    """Normalize a config file path into a filesystem-safe folder name.

    Uses the file stem, lowercased with non-alphanumeric characters
    collapsed to hyphens, suffixed with a short hash of the original
    (unmodified) stem to avoid collisions between configs that
    normalize to the same slug.
    """
    stem = Path(config_path).stem
    slug = re.sub(r"[^a-z0-9]+", "-", stem.lower()).strip("-")
    if not slug:
        slug = "config"
    digest = hashlib.sha256(stem.encode()).hexdigest()[:8]
    return f"{slug}-{digest}"


def runs_dir_for_config(config_path: str) -> Path:
    return Path.cwd() / ASSERTLLM_DIR / RUNS_DIR / config_to_folder(config_path)


def all_run_files(config_path: str) -> list[Path]:
    """Run files for a config, sorted ascending by run number."""
    runs_dir = runs_dir_for_config(config_path)
    if not runs_dir.exists():
        return []
    files = [p for p in runs_dir.glob("*.json") if p.stem.isdigit()]
    return sorted(files, key=lambda p: int(p.stem))


def next_run_number(config_path: str) -> int:
    files = all_run_files(config_path)
    if not files:
        return 1
    return max(int(f.stem) for f in files) + 1


def resolve_run_number(config_path: str, n: int) -> Path | None:
    """Resolve a run number to a file.

    Positive n refers to the literal run number (filename). Negative n
    is a relative index from the end, e.g. -1 is the latest run, -2 is
    the run before that. 0 is invalid.
    """
    if n == 0:
        return None

    files = all_run_files(config_path)
    if not files:
        return None

    if n < 0:
        idx = len(files) + n
        if 0 <= idx < len(files):
            return files[idx]
        return None

    for f in files:
        if int(f.stem) == n:
            return f
    return None


def load_run(path: Path) -> dict:
    with open(path) as f:
        return json.load(f)