import json
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from assertllm.models.schema import Config, TestConfig
from assertllm.caller.http import call_endpoint
from assertllm.judges import get_judge
from assertllm.judges.base import BaseJudge


@dataclass
class AssertionResult:
    assertion: str
    passed: bool


@dataclass
class TestResult:
    name: str
    input: dict
    assertion_results: list[AssertionResult] = field(default_factory=list)
    response: str | None = None
    error: str | None = None
    duration_ms: int = 0

    @property
    def is_error(self) -> bool:
        return self.error is not None

    @property
    def passed(self) -> bool:
        return not self.is_error and all(r.passed for r in self.assertion_results)

    @property
    def pass_count(self) -> int:
        return sum(1 for r in self.assertion_results if r.passed)

    @property
    def total_count(self) -> int:
        return len(self.assertion_results)


def _run_test(test: TestConfig, judge: BaseJudge) -> TestResult:
    start = time.monotonic()
    try:
        response = call_endpoint(test)
        verdicts = judge.evaluate(response, test.assertions)
        assertion_results = [
            AssertionResult(assertion=a, passed=v)
            for a, v in zip(test.assertions, verdicts)
        ]
        duration_ms = int((time.monotonic() - start) * 1000)
        return TestResult(
            name=test.name,
            input=test.body,
            response=response,
            assertion_results=assertion_results,
            duration_ms=duration_ms,
        )
    except Exception as e:
        duration_ms = int((time.monotonic() - start) * 1000)
        return TestResult(
            name=test.name,
            input=test.body,
            error=str(e),
            duration_ms=duration_ms,
        )


def _save_run(config_path: str, results: list[TestResult]) -> Path:
    stem = Path(config_path).stem
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    runs_dir = Path.cwd() / "runs"
    runs_dir.mkdir(exist_ok=True)
    run_file = runs_dir / f"{stem}_{timestamp}.json"

    record = {
        "run_id": f"{stem}_{timestamp}",
        "config": config_path,
        "timestamp": datetime.now().isoformat(),
        "tests": [
            {
                "name": r.name,
                "is_error": r.is_error,
                "error": r.error,
                "input": r.input,
                "response": r.response,
                "duration_ms": r.duration_ms,
                "assertions": (
                    None if r.is_error else
                    [{"assertion": a.assertion, "passed": a.passed} for a in r.assertion_results]
                ),
            }
            for r in results
        ],
    }

    with open(run_file, "w") as f:
        json.dump(record, f, indent=2)

    return run_file


def run(config: Config, config_path: str) -> tuple[list[TestResult], Path]:
    judge = get_judge(config.judge)
    results = [_run_test(test, judge) for test in config.tests]
    run_file = _save_run(config_path, results)
    return results, run_file