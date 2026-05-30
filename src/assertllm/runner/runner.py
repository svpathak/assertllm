from dataclasses import dataclass, field
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
    assertion_results: list[AssertionResult] = field(default_factory=list)
    error: str | None = None

    @property
    def passed(self) -> bool:
        return self.error is None and all(r.passed for r in self.assertion_results)

    @property
    def pass_count(self) -> int:
        return sum(1 for r in self.assertion_results if r.passed)

    @property
    def total_count(self) -> int:
        return len(self.assertion_results)


def _run_test(test: TestConfig, judge: BaseJudge) -> TestResult:
    try:
        response = call_endpoint(test)
        verdicts = judge.evaluate(response, test.assertions)
        assertion_results = [
            AssertionResult(assertion=a, passed=v)
            for a, v in zip(test.assertions, verdicts)
        ]
        return TestResult(name=test.name, assertion_results=assertion_results)
    except Exception as e:
        return TestResult(name=test.name, error=str(e))


def run(config: Config) -> list[TestResult]:
    judge = get_judge(config.judge)
    return [_run_test(test, judge) for test in config.tests]