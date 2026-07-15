from assertllm.reporter.terminal import report
from assertllm.models.results import AssertionResult, TestResult


def _passing_result(name="t"):
    return TestResult(
        name=name,
        input={},
        response="ok",
        assertion_results=[
            AssertionResult(assertion="a", passed=True),
            AssertionResult(assertion="b", passed=True)
        ]
    )


def _failing_result(name="t"):
    return TestResult(
        name=name,
        input={},
        response="ok",
        assertion_results=[
            AssertionResult(assertion="a", passed=True),
            AssertionResult(assertion="b", passed=False)
        ]
    )


def _error_result(name="t"):
    return TestResult(name=name, input={}, error="connection refused")


def test_report_exit_code_zero_when_all_pass():
    assert report([_passing_result(), _passing_result("t2")]) == 0


def test_report_exit_code_one_when_any_fails():
    assert report([_passing_result(), _failing_result("t2")]) == 1


def test_report_exit_code_one_when_any_errors():
    assert report([_passing_result(), _error_result("t2")]) == 1


def test_report_exit_code_zero_when_no_results():
    assert report([]) == 0


def test_report_prints_pass_line(capsys):
    report([_passing_result("refund policy")])
    out = capsys.readouterr().out
    assert "PASS" in out
    assert "refund policy" in out
    assert "2/2 passed" in out


def test_report_prints_fail_line_with_failed_assertion_detail(capsys):
    report([_failing_result("summarizer")])
    out = capsys.readouterr().out
    assert "FAIL" in out
    assert "summarizer" in out
    assert "1/2 passed" in out
    assert "-> b" in out


def test_report_does_not_print_passed_assertions_as_detail_lines(capsys):
    report([_failing_result("summarizer")])
    out = capsys.readouterr().out
    assert "-> a" not in out


def test_report_prints_error_line_with_error_message(capsys):
    report([_error_result("bad auth")])
    out = capsys.readouterr().out
    assert "FAIL" in out
    assert "bad auth" in out
    assert "connection refused" in out


def test_report_prints_final_summary_counts(capsys):
    report([_passing_result("a"), _failing_result("b"), _error_result("c")])
    out = capsys.readouterr().out
    assert "1 passed" in out
    assert "2 failed" in out