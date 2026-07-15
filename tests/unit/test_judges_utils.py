import pytest
from assertllm.judges.utils import JudgeUtils


def test_build_prompt_includes_response():
    prompt = JudgeUtils.build_prompt("the refund window is 30 days", ["mentions 30 days"])
    assert "the refund window is 30 days" in prompt


def test_build_prompt_numbers_assertions_in_order():
    prompt = JudgeUtils.build_prompt("ok", ["first assertion", "second assertion", "third assertion"])
    assert "1. first assertion" in prompt
    assert "2. second assertion" in prompt
    assert "3. third assertion" in prompt


def test_build_prompt_format_section_matches_assertion_count():
    prompt = JudgeUtils.build_prompt("ok", ["a", "b"])
    assert "1. YES or NO" in prompt
    assert "2. YES or NO" in prompt
    assert "3. YES or NO" not in prompt


def test_parse_response_all_yes():
    result = JudgeUtils.parse_response("1. YES\n2. YES\n3. YES", 3)
    assert result == [True, True, True]


def test_parse_response_mixed():
    result = JudgeUtils.parse_response("1. YES\n2. NO\n3. YES", 3)
    assert result == [True, False, True]


def test_parse_response_case_insensitive():
    result = JudgeUtils.parse_response("1. yes\n2. no", 2)
    assert result == [True, False]


def test_parse_response_ignores_blank_lines():
    result = JudgeUtils.parse_response("1. YES\n\n2. NO\n\n", 2)
    assert result == [True, False]


def test_parse_response_ignores_leading_trailing_whitespace_per_line():
    result = JudgeUtils.parse_response("   1. YES   \n   2. NO   ", 2)
    assert result == [True, False]


def test_parse_response_too_few_answers_raises():
    with pytest.raises(ValueError, match="Expected 3 judgments, got 2"):
        JudgeUtils.parse_response("1. YES\n2. NO", 3)


def test_parse_response_too_many_answers_raises():
    with pytest.raises(ValueError, match="Expected 1 judgments, got 2"):
        JudgeUtils.parse_response("1. YES\n2. NO", 1)


def test_parse_response_empty_text_raises():
    with pytest.raises(ValueError, match="Expected 1 judgments, got 0"):
        JudgeUtils.parse_response("", 1)


def test_parse_response_line_with_neither_yes_nor_no_is_skipped():
    # a stray commentary line without YES/NO is silently dropped, which can
    # shift the count and is worth documenting via this test
    result = JudgeUtils.parse_response("Sure, here are my answers:\n1. YES\n2. NO", 2)
    assert result == [True, False]