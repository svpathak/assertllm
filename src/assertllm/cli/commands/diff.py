import sys
import typer
from rich.text import Text
from assertllm.cli.errors import exit_with_error
from assertllm.cli.utils import console, all_run_files, resolve_run_number, load_run


def diff_command(
    config: str = typer.Option(..., "--config", "-c", help="Path to the YAML config file"),
    base: int | None = typer.Option(None, "--base", help="Run number to use as baseline"),
    head: int | None = typer.Option(None, "--head", help="Run number to compare against baseline")
) -> None:
    if head is not None and base is None:
        exit_with_error(
            "--head cannot be used without --base.\n"
            "Specify --base to set the baseline."
        )

    runs = all_run_files(config)
    if not runs:
        exit_with_error(
            f"No runs found for this config.\n"
            f"Run 'assertllm run {config}' at least twice first."
        )

    base_n = base if base is not None else -2
    head_n = head if head is not None else -1

    base_file = resolve_run_number(config, base_n)
    head_file = resolve_run_number(config, head_n)

    if base_file is None or head_file is None:
        if len(runs) < 2:
            exit_with_error(
                f"Need at least 2 runs for this config to diff. Only 1 run found.\n"
                f"Run 'assertllm run {config}' again to create another run."
            )
        missing = base_n if base_file is None else head_n
        exit_with_error(f"No run #{missing} found for this config.")

    if base_file == head_file:
        exit_with_error(
            f"--base and --head resolve to the same run (#{load_run(base_file)['run_id']}).\n"
            f"Run 'assertllm run {config}' again to create another run to compare against."
        )

    base_record = load_run(base_file)
    head_record = load_run(head_file)

    console.print(f"\nBase: #{base_record['run_id']}  {base_record.get('timestamp')}")
    console.print(f"Head: #{head_record['run_id']}  {head_record.get('timestamp')}")
    console.print()

    base_tests = {t["name"]: t for t in base_record.get("tests", [])}
    head_tests = {t["name"]: t for t in head_record.get("tests", [])}
    all_names = list(base_tests.keys() | head_tests.keys())

    drifted = False

    for name in all_names:
        t_base = base_tests.get(name)
        t_head = head_tests.get(name)

        if t_base is None:
            console.print(Text(f"NEW   {name}", style="yellow"))
            continue

        if t_head is None:
            console.print(Text(f"GONE  {name}", style="yellow"))
            continue

        if t_base.get("is_error") or t_head.get("is_error"):
            console.print(Text(f"SKIP  {name} -- one or both runs captured an error", style="dim"))
            continue

        a_base = {a["assertion"]: a["passed"] for a in (t_base.get("assertions") or [])}
        a_head = {a["assertion"]: a["passed"] for a in (t_head.get("assertions") or [])}

        flipped = [
            (assertion, a_base[assertion], a_head[assertion])
            for assertion in a_base
            if assertion in a_head and a_base[assertion] != a_head[assertion]
        ]

        if not flipped:
            console.print(Text(f"OK    {name}", style="green"))
        else:
            drifted = True
            console.print(Text(f"DRIFT {name}", style="red"))
            for assertion, before, after in flipped:
                b = "PASS" if before else "FAIL"
                a = "PASS" if after else "FAIL"
                console.print(f"      -> {assertion}  ({b} -> {a})", style="dim")

    console.print()
    sys.exit(1 if drifted else 0)