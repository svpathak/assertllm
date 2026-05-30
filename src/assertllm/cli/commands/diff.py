import json
import sys
import typer
from pathlib import Path
from assertllm.config.loader import load_config
from assertllm.config.validator import validate_config
from assertllm.caller.http import call_endpoint
from assertllm.judges import get_judge
from rich.console import Console

console = Console()


def _latest_snapshot(stem: str) -> Path | None:
    snapshots_dir = Path.cwd() / "snapshots"
    if not snapshots_dir.exists():
        return None
    matches = sorted(snapshots_dir.glob(f"{stem}_*.json"), reverse=True)
    return matches[0] if matches else None


def diff_command(
    config_path: str = typer.Argument(..., help="Path to the YAML config file"),
    snapshot_path: str | None = typer.Option(None, "--snapshot", "-s", help="Path to snapshot file (defaults to latest)"),
) -> None:
    config = load_config(config_path)
    validate_config(config)

    stem = Path(config_path).stem
    resolved = Path(snapshot_path) if snapshot_path else _latest_snapshot(stem)

    if resolved is None:
        typer.echo(f"No snapshot found for '{stem}'. Run: assertllm snapshot {config_path}")
        raise typer.Exit(1)

    typer.echo(f"Comparing against: {resolved}")

    with open(resolved, "r") as f:
        snapshot = json.load(f)

    judge = get_judge(config.judge)
    drifted = False

    console.print()
    for test in config.tests:
        if test.name not in snapshot:
            console.print(f"[yellow]SKIP[/yellow] {test.name} -- not in snapshot")
            continue

        baseline = snapshot[test.name]
        if baseline["error"]:
            console.print(f"[yellow]SKIP[/yellow] {test.name} -- snapshot captured an error")
            continue

        try:
            current_response = call_endpoint(test)
        except Exception as e:
            console.print(f"[red]FAIL[/red] {test.name} -- error: {e}")
            drifted = True
            continue

        baseline_verdicts = judge.evaluate(baseline["response"], test.assertions)
        current_verdicts = judge.evaluate(current_response, test.assertions)

        changed = [
            (a, b, c)
            for a, b, c in zip(test.assertions, baseline_verdicts, current_verdicts)
            if b != c
        ]

        if not changed:
            console.print(f"[green]OK  [/green] {test.name} -- no drift")
        else:
            drifted = True
            console.print(f"[red]DRIFT[/red] {test.name}")
            for assertion, baseline_val, current_val in changed:
                before = "PASS" if baseline_val else "FAIL"
                after = "PASS" if current_val else "FAIL"
                console.print(f"     -> {assertion}  ({before} -> {after})", style="dim")

    console.print()
    sys.exit(1 if drifted else 0)