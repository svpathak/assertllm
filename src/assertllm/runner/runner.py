import json
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from assertllm.models.schema import Config, TestConfig
from assertllm.models.results import AssertionResult, TestResult
from assertllm.caller.http import call_endpoint
from assertllm.judges import get_judge
from assertllm.judges.base import BaseJudge
from assertllm.storage.runs import runs_dir_for_config, next_run_number, ensure_assertllm_gitignore


def _run_test(test: TestConfig, judge: BaseJudge) -> TestResult:
    start = time.monotonic()
    try:
        status_code, response = call_endpoint(test)
        duration_ms = int((time.monotonic() - start) * 1000)

        if test.expected_status is not None:
            if status_code != test.expected_status:
                return TestResult(
                    name=test.name,
                    input=test.body,
                    status_code=status_code,
                    error=f"expected status {test.expected_status}, got {status_code}",
                    duration_ms=duration_ms
                )
        elif not (200 <= status_code < 300):
            return TestResult(
                name=test.name,
                input=test.body,
                status_code=status_code,
                error=f"unexpected status {status_code}",
                duration_ms=duration_ms
            )

        verdicts = judge.evaluate(response, test.assertions)
        assertion_results = [
            AssertionResult(assertion=a, passed=v)
            for a, v in zip(test.assertions, verdicts)
        ]
        return TestResult(
            name=test.name,
            input=test.body,
            response=response,
            status_code=status_code,
            assertion_results=assertion_results,
            duration_ms=duration_ms
        )
    except Exception as e:
        duration_ms = int((time.monotonic() - start) * 1000)
        return TestResult(
            name=test.name,
            input=test.body,
            error=str(e),
            duration_ms=duration_ms
        )

def _save_run(config_path: str, results: list[TestResult]) -> tuple[Path, int]:
    ensure_assertllm_gitignore()
    runs_dir = runs_dir_for_config(config_path)
    runs_dir.mkdir(parents=True, exist_ok=True)

    run_number = next_run_number(config_path)
    run_file = runs_dir / f"{run_number}.json"

    record = {
        "run_id": run_number,
        "config": config_path,
        "timestamp": datetime.now().isoformat(),
        "tests": [
            {
                "name": r.name,
                "is_error": r.is_error,
                "error": r.error,
                "status_code": r.status_code,
                "input": r.input,
                "response": r.response,
                "duration_ms": r.duration_ms,
                "assertions": (
                    None if r.is_error else
                    [{"assertion": a.assertion, "passed": a.passed} for a in r.assertion_results]
                )
            }
            for r in results
        ],
    }

    with open(run_file, "w") as f:
        json.dump(record, f, indent=2)

    return run_file, run_number


def run(config: Config, config_path: str) -> tuple[list[TestResult], Path, int]:
    judge = get_judge(config.judge)
    results = [_run_test(test, judge) for test in config.tests]
    run_file, run_number = _save_run(config_path, results)
    return results, run_file, run_number