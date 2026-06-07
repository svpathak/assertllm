import typer
from assertllm.cli.commands.run import run_command
from assertllm.cli.commands.diff import diff_command
from assertllm.cli.commands.inspect import inspect_command

app = typer.Typer()
app.command("run")(run_command)
app.command("diff")(diff_command)
app.command("inspect")(inspect_command)