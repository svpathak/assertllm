import json
import typer
from datetime import datetime
from pathlib import Path
from assertllm.config.loader import load_config
from assertllm.config.validator import validate_config
from assertllm.caller.http import call_endpoint


def snapshot_command(
    config_path: str = typer.Argument(..., help="Path to the YAML config file"),
) -> None:
    config = load_config(config_path)
    validate_config(config)

    stem = Path(config_path).stem
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    snapshots_dir = Path.cwd() / "snapshots"
    snapshots_dir.mkdir(exist_ok=True)
    output = snapshots_dir / f"{stem}_{timestamp}.json"

    snapshot = {}
    for test in config.tests:
        try:
            response = call_endpoint(test)
            snapshot[test.name] = {"response": response, "error": None}
        except Exception as e:
            snapshot[test.name] = {"response": None, "error": str(e)}

    with open(output, "w") as f:
        json.dump(snapshot, f, indent=2)

    typer.echo(f"Snapshot written to {output}")