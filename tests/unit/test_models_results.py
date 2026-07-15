from assertllm.models.results import AssertionResult, TestResult

def test_is_error_true_when_error_set():
    r = TestResult(name="t", input={}, error="boom")
    assert r.is_error is True


def test_is_error_false_when_no_error():
    r = TestResult(name="t", input={}, response="ok")
    assert r.is_error is False


def test_passed_false_when_error():
    r = TestResult(
        name="t",
        input={},
        error="boom",
        assertion_results=[AssertionResult(assertion="a", passed=True)]
    )
    assert r.passed is False


def test_passed_true_when_all_assertions_pass():
    r = TestResult(
        name="t",
        input={},
        response="ok",
        assertion_results=[
            AssertionResult(assertion="a", passed=True),
            AssertionResult(assertion="b", passed=True)
        ]
    )
    assert r.passed is True


def test_passed_false_when_any_assertion_fails():
    r = TestResult(
        name="t",
        input={},
        response="ok",
        assertion_results=[
            AssertionResult(assertion="a", passed=True),
            AssertionResult(assertion="b", passed=False)
        ]
    )
    assert r.passed is False


def test_passed_true_when_no_assertions_and_no_error():
    r = TestResult(name="t", input={}, response="ok")
    assert r.passed is True


def test_pass_count_and_total_count():
    r = TestResult(
        name="t",
        input={},
        response="ok",
        assertion_results=[
            AssertionResult(assertion="a", passed=True),
            AssertionResult(assertion="b", passed=False),
            AssertionResult(assertion="c", passed=True)
        ]
    )
    assert r.pass_count == 2
    assert r.total_count == 3


def test_status_code_defaults_to_none():
    r = TestResult(name="t", input={})
    assert r.status_code is None


def test_status_code_can_be_set():
    r = TestResult(name="t", input={}, status_code=401)
    assert r.status_code == 401