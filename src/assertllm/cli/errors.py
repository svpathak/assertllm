import typer
from rich.console import Console
from rich.panel import Panel

console = Console(stderr=True)


def exit_with_error(message: str) -> None:
    console.print(Panel(message, title="Error", border_style="red"))
    raise typer.Exit(1)