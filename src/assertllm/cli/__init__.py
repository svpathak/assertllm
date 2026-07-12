import typer
from assertllm.cli.commands.run import run_command
from assertllm.cli.commands.diff import diff_command
from assertllm.cli.commands.inspect import inspect_command

app = typer.Typer(
    help="Fire inputs at AI endpoints and evaluate outputs using plain-English assertions.",
    add_completion=False,
    context_settings={"help_option_names": ["--help", "-h"]}
)
app.command("run")(run_command)
app.command("diff")(diff_command)
app.command("inspect")(inspect_command)