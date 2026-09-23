from unittest.mock import patch
from assertllm.runner.runner import _run_test, run
from assertllm.models.schema import TestConfig, Config, JudgeConfig
from assertllm.judges.base import BaseJudge


def _test_config(**overrides):
    kwargs = {
        "name": "sample",
        "endpoint": "https://example.com/chat",
        "body": {"message": "hi"},
        "assert": ["is polite", "mentions refund"]
    }
    kwargs.update(overrides)
    return TestConfig(**kwargs)


class FakeJudge(BaseJudge):
    def __init__(self, verdicts):
        self.verdicts = verdicts

    def evaluate(self, response, assertions):
        return self.verdicts


def test_no_expected_status_2xx_reaches_judge():
    test = _test_config()
    judge = FakeJudge([True, True])
    with patch("assertllm.runner.runner.call_endpoint", return_value=(200, "the refund policy is generous")):
        result = _run_test(test, judge)
    assert result.is_error is False
    assert result.status_code == 200
    assert result.pass_count == 2
    assert result.total_count == 2


def test_no_expected_status_4xx_is_error():
    test = _test_config()
    judge = FakeJudge([True, True])
    with patch("assertllm.runner.runner.call_endpoint", return_value=(404, "not found")):
        result = _run_test(test, judge)
    assert result.is_error is True
    assert result.status_code == 404
    assert "unexpected status 404" in result.error


def test_expected_status_match_reaches_judge():
    test = _test_config(expected_status=401)
    judge = FakeJudge([True])
    with patch("assertllm.runner.runner.call_endpoint", return_value=(401, "unauthorized access")):
        result = _run_test(test, judge)
    assert result.is_error is False
    assert result.status_code == 401
    assert result.pass_count == 1


def test_expected_status_mismatch_is_error():
    test = _test_config(expected_status=401)
    judge = FakeJudge([True])
    with patch("assertllm.runner.runner.call_endpoint", return_value=(200, "ok")):
        result = _run_test(test, judge)
    assert result.is_error is True
    assert result.status_code == 200
    assert "expected status 401, got 200" in result.error


def test_caller_exception_is_captured_as_error():
    test = _test_config()
    judge = FakeJudge([True])
    with patch("assertllm.runner.runner.call_endpoint", side_effect=ConnectionError("timed out")):
        result = _run_test(test, judge)
    assert result.is_error is True
    assert "timed out" in result.error
    assert result.status_code is None


def test_judge_never_called_when_status_check_fails():
    test = _test_config(expected_status=401)
    judge = FakeJudge([True])
    with patch("assertllm.runner.runner.call_endpoint", return_value=(200, "ok")), \
         patch.object(judge, "evaluate") as mock_evaluate:
        _run_test(test, judge)
    mock_evaluate.assert_not_called()


def test_run_saves_results_and_returns_run_number(isolated_cwd):
    config = Config(
        judge=JudgeConfig(provider="ollama", model="llama3"),
        tests=[_test_config()],
    )
    judge = FakeJudge([True, True])
    with patch("assertllm.runner.runner.get_judge", return_value=judge), \
         patch("assertllm.runner.runner.call_endpoint", return_value=(200, "ok, refund granted")):
        results, run_file, run_number = run(config, "sample.yaml")
    assert run_number == 1
    assert run_file.exists()
    assert len(results) == 1
    assert results[0].passed is True


def test_run_creates_assertllm_gitignore(isolated_cwd):
    config = Config(
        judge=JudgeConfig(provider="ollama", model="llama3"),
        tests=[_test_config()],
    )
    judge = FakeJudge([True, True])
    with patch("assertllm.runner.runner.get_judge", return_value=judge), \
         patch("assertllm.runner.runner.call_endpoint", return_value=(200, "ok, refund granted")):
        run(config, "sample.yaml")
    gitignore_path = isolated_cwd / ".assertllm" / ".gitignore"
    assert gitignore_path.exists()
    assert gitignore_path.read_text() == "*\n"