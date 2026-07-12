from dataclasses import dataclass, field


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
    status_code: int | None = None
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