import json
from pathlib import Path
from rich.console import Console

console = Console()


def all_runs(stem: str | None) -> list[Path]:
    runs_dir = Path.cwd() / "runs"
    if not runs_dir.exists():
        return []
    pattern = f"{stem}_*.json" if stem else "*.json"
    return sorted(
        runs_dir.glob(pattern),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )


def latest_run(stem: str | None) -> Path | None:
    matches = all_runs(stem)
    return matches[0] if matches else None


def load_run(path: Path) -> dict:
    with open(path) as f:
        return json.load(f)