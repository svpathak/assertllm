import json
import typer
from pathlib import Path
from rich.console import Console
from rich.text import Text

console = Console()


def _latest_run(stem: str | None) -> Path | None:
    runs_dir = Path.cwd() / "runs"
    if not runs_dir.exists():
        return None
    pattern = f"{stem}_*.json" if stem else "*.json"
    matches = sorted(runs_dir.glob(pattern), reverse=True)
    return matches[0] if matches else None


def _render_test(test: dict) -> None:
    name = test["name"]
    is_error = test["is_error"]

    console.print()

    if is_error:
        line = Text()
        line.append("ERROR ", style="bold red")
        line.append(name)
        console.print(line)
        console.print(f"  error:    {test['error']}", style="dim")
        console.print(f"  input:    {json.dumps(test['input'])}", style="dim")
        console.print(f"  duration: {test['duration_ms']}ms", style="dim")
        return

    assertions = test["assertions"] or []
    passed = sum(1 for a in assertions if a["passed"])
    total = len(assertions)
    status = "PASS" if passed == total else "FAIL"
    style = "bold green" if passed == total else "bold red"

    line = Text()
    line.append(f"{status} ", style=style)
    line.append(f"{name} -- {passed}/{total} passed")
    console.print(line)
    console.print(f"  input:    {json.dumps(test['input'])}", style="dim")
    console.print(f"  response: {test['response']}", style="dim")
    console.print(f"  duration: {test['duration_ms']}ms", style="dim")
    console.print("  assertions:", style="dim")
    for a in assertions:
        symbol = "PASS" if a["passed"] else "FAIL"
        style = "green" if a["passed"] else "red"
        console.print(f"    [{symbol}] {a['assertion']}", style=style)


def inspect_command(
    run_path: str | None = typer.Option(None, "--run", "-r", help="Path to a specific run file"),
    test: str | None = typer.Option(None, "--test", "-t", help="Filter to a specific test by name"),
    config: str | None = typer.Option(None, "--config", "-c", help="Filter runs by config file name"),
) -> None:
    if run_path:
        resolved = Path(run_path)
    else:
        stem = Path(config).stem if config else None
        resolved = _latest_run(stem)

    if resolved is None or not resolved.exists():
        typer.echo("No run file found. Run: assertllm run config.yaml first")
        raise typer.Exit(1)

    with open(resolved, "r") as f:
        record = json.load(f)

    console.print(f"\nRun:    {record['run_id']}")
    console.print(f"Config: {record['config']}")
    console.print(f"Time:   {record['timestamp']}")

    tests = record["tests"]
    if test:
        tests = [t for t in tests if t["name"] == test]
        if not tests:
            typer.echo(f"No test named '{test}' in this run")
            raise typer.Exit(1)

    for t in tests:
        _render_test(t)

    console.print()