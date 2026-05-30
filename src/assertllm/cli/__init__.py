import typer
from assertllm.cli.commands.run import run_command
from assertllm.cli.commands.snapshot import snapshot_command
from assertllm.cli.commands.diff import diff_command

app = typer.Typer()
app.command("run")(run_command)
app.command("snapshot")(snapshot_command)
app.command("diff")(diff_command)