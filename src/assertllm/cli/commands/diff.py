import sys
import typer
from pathlib import Path
from rich.text import Text
from assertllm.cli.errors import exit_with_error
from assertllm.cli.utils import console, all_runs, load_run


def diff_command(
    config_path: str = typer.Argument(..., help="Path to the YAML config file"),
    base_path: str | None = typer.Option(None, "--base", help="Older run to use as baseline"),
    head_path: str | None = typer.Option(None, "--head", help="Newer run to compare against baseline")
) -> None:
    stem = Path(config_path).stem

    if head_path and not base_path:
        exit_with_error(
            "--head cannot be used without --base.\n"
            "Specify --base to set the baseline, or use --base alone to compare against the latest run."
        )

    elif base_path and head_path:
        base_file = Path(base_path)
        head_file = Path(head_path)
        if not base_file.exists():
            exit_with_error(f"Run file not found: {base_path}")
        if not head_file.exists():
            exit_with_error(f"Run file not found: {head_path}")
        if base_file == head_file:
            exit_with_error("--base and --head point to the same file.")
        base = load_run(base_file)
        head = load_run(head_file)
        if base.get("config") != head.get("config"):
            exit_with_error(
                f"Runs belong to different configs.\n"
                f"  {base_file.name} -> {base.get('config')}\n"
                f"  {head_file.name} -> {head.get('config')}"
            )

    elif base_path:
        base_file = Path(base_path)
        if not base_file.exists():
            exit_with_error(f"Run file not found: {base_path}")
        base = load_run(base_file)
        all_sorted = all_runs(stem)
        if not all_sorted:
            exit_with_error(f"No runs found for '{stem}'.")
        head_file = all_sorted[0]
        if head_file == base_file:
            exit_with_error(
                f"Not enough runs for '{stem}' to diff.\n"
                f"Only one run exists. Run 'assertllm run {config_path}' again to create a second run."
            )
        head = load_run(head_file)
        if head.get("config") != base.get("config"):
            exit_with_error(
                f"Latest run belongs to a different config than --base.\n"
                f"  base: {base_file.name} -> {base.get('config')}\n"
                f"  head: {head_file.name} -> {head.get('config')}\n"
                f"Specify --head explicitly to choose a matching run."
            )

    else:
        all_sorted = all_runs(stem)
        if not all_sorted:
            exit_with_error(
                f"No runs found for '{stem}'.\n"
                f"Run 'assertllm run {config_path}' at least twice first."
            )
        head_file = all_sorted[0]
        head = load_run(head_file)
        head_config = head.get("config")
        candidates = [r for r in all_sorted[1:] if load_run(r).get("config") == head_config]
        if not candidates:
            exit_with_error(
                f"Not enough runs for '{stem}' with the same config to diff.\n"
                f"Run 'assertllm run {config_path}' again to create a second run."
            )
        base_file = candidates[0]
        base = load_run(base_file)

    console.print(f"\nBase: {base.get('timestamp')}  ({base_file.name})")
    console.print(f"Head: {head.get('timestamp')}  ({head_file.name})")
    console.print()

    base_tests = {t["name"]: t for t in base.get("tests", [])}
    head_tests = {t["name"]: t for t in head.get("tests", [])}
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