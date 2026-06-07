import json
import typer
from pathlib import Path
from rich.text import Text
from assertllm.cli.errors import exit_with_error
from assertllm.cli.utils import console, all_runs, latest_run, load_run


def _validate_args(
    run_path: str | None,
    config: str | None,
    test: str | None,
    list_runs: bool
) -> None:
    if list_runs and run_path:
        exit_with_error(
            "--list and --run cannot be used together.\n"
            "--list shows available runs. --run inspects a specific one."
        )

    if list_runs and test:
        exit_with_error(
            "--list and --test cannot be used together.\n"
            "--list shows available runs. Use --run or --config with --test to inspect a specific run."
        )

    if run_path and config:
        exit_with_error(
            "--run and --config cannot be used together.\n"
            "--run points to a specific file directly.\n"
            "Use --config only when you want the latest run for a given config."
        )

    if test and not run_path and not config:
        exit_with_error(
            "--test requires either --run or --config.\n"
            "Use --run to point to a specific file, or --config to use the latest run for that config."
        )


def _render_list(runs: list[Path]) -> None:
    if not runs:
        console.print("No runs found.", style="dim")
        return

    for run_path in runs:
        try:
            console.print(run_path.relative_to(Path.cwd()))
        except ValueError:
            console.print(run_path)


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
    list_runs_flag: bool = typer.Option(False, "--list", "-l", help="List all saved runs")
) -> None:
    _validate_args(run_path, config, test, list_runs_flag)

    if list_runs_flag:
        stem = Path(config).stem if config else None
        _render_list(all_runs(stem))
        return

    if run_path:
        resolved = Path(run_path)
    else:
        stem = Path(config).stem if config else None
        resolved = latest_run(stem)

    if resolved is None or not resolved.exists():
        exit_with_error("No run file found. Run 'assertllm run config.yaml' first.")

    record = load_run(resolved)

    console.print(f"\nRun:    {record['run_id']}")
    console.print(f"Config: {record['config']}")
    console.print(f"Time:   {record['timestamp']}")

    tests = record["tests"]
    if test:
        tests = [t for t in tests if t["name"] == test]
        if not tests:
            exit_with_error(f"No test named '{test}' in this run.")

    for t in tests:
        _render_test(t)

    console.print()