import sys
import typer
from assertllm.config.loader import load_config
from assertllm.config.validator import validate_config
from assertllm.runner.runner import run
from assertllm.reporter.terminal import report


def run_command(
    config_path: str = typer.Argument(..., help="Path to the YAML config file"),
    test: str | None = typer.Option(None, "--test", help="Run a single test by name"),
) -> None:
    config = load_config(config_path)
    validate_config(config)

    if test:
        matched = [t for t in config.tests if t.name == test]
        if not matched:
            typer.echo(f"No test named '{test}' found in config")
            raise typer.Exit(1)
        config.tests = matched

    results = run(config)
    exit_code = report(results)
    sys.exit(exit_code)