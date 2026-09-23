from rich.console import Console
from rich.text import Text
from assertllm.models.results import TestResult

console = Console()


def _render_test(result: TestResult) -> None:
    if result.error:
        line = Text()
        line.append("FAIL ", style="bold red")
        line.append(f"{result.name} -- error: {result.error}")
        console.print(line)
        return

    summary = f"{result.pass_count}/{result.total_count} passed"
    if result.passed:
        line = Text()
        line.append("PASS ", style="bold green")
        line.append(f"{result.name} -- {summary}")
        console.print(line)
    else:
        line = Text()
        line.append("FAIL ", style="bold red")
        line.append(f"{result.name} -- {summary}")
        console.print(line)
        for ar in result.assertion_results:
            if not ar.passed:
                console.print(f"     -> {ar.assertion}", style="dim")


def report(results: list[TestResult]) -> int:
    console.print()
    for result in results:
        _render_test(result)
    console.print()

    total = len(results)
    passed = sum(1 for r in results if r.passed)
    failed = total - passed

    summary = Text()
    summary.append(f"{passed} passed", style="green")
    summary.append(", ")
    summary.append(f"{failed} failed", style="red" if failed else "dim")
    console.print(summary)
    console.print()

    return 0 if failed == 0 else 1