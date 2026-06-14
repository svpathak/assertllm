import json
import typer
from rich.text import Text
from assertllm.cli.errors import exit_with_error
from assertllm.cli.utils import console, all_run_files, resolve_run_number, load_run


def _validate_args(run_number: int | None, test: str | None, list_runs: bool) -> None:
    if list_runs and run_number is not None:
        exit_with_error(
            "--list and --run cannot be used together.\n"
            "--list shows available runs. --run inspects a specific one."
        )

    if list_runs and test:
        exit_with_error(
            "--list and --test cannot be used together.\n"
            "--list shows available runs. Use --run with --test to inspect a specific run."
        )


def _build_summary(tests: list[dict]) -> Text:
    total = len(tests)
    errors = sum(1 for t in tests if t.get("is_error"))
    passed = sum(
        1 for t in tests
        if not t.get("is_error") and all(a["passed"] for a in (t.get("assertions") or []))
    )
    failed = total - passed - errors

    summary = Text(f"{total} tests -- ")
    if passed:
        summary.append(f"{passed} passed", style="green")
    if failed:
        if passed:
            summary.append(", ")
        summary.append(f"{failed} failed", style="red")
    if errors:
        if passed or failed:
            summary.append(", ")
        summary.append(f"{errors} error", style="red")
    if not passed and not failed and not errors:
        summary.append("0 passed", style="dim")
    return summary


def _render_list(config: str) -> None:
    files = all_run_files(config)
    if not files:
        console.print("No runs found for this config.", style="dim")
        return

    for f in reversed(files):
        record = load_run(f)
        tests = record.get("tests", [])
        line = Text(f"#{record.get('run_id')}  {record.get('timestamp')}  ")
        line.append_text(_build_summary(tests))
        console.print(line)


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
    config: str = typer.Option(..., "--config", "-c", help="Path to the YAML config file"),
    run_number: int | None = typer.Option(None, "--run", "-r", help="Run number. Negative values count from the latest, e.g. -1 is the latest run"),
    test: str | None = typer.Option(None, "--test", "-t", help="Filter to a specific test by name"),
    list_runs_flag: bool = typer.Option(False, "--list", "-l", help="List all saved runs for this config")
) -> None:
    _validate_args(run_number, test, list_runs_flag)

    if list_runs_flag:
        _render_list(config)
        return

    n = run_number if run_number is not None else -1
    resolved = resolve_run_number(config, n)

    if resolved is None:
        exit_with_error(
            f"No run #{n} found for this config.\n"
            f"Run 'assertllm run {config}' first, or use --list to see available runs."
        )

    record = load_run(resolved)

    console.print(f"\nRun:    #{record['run_id']}")
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