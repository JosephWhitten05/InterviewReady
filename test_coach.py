from coach import (check_answer, check_posting, parse_json,
                   validate_feedback, validate_questions)


GOOD = {
    "scores": {"relevance": 4, "structure": 3, "clarity": 4, "concision": 5},
    "strength": "Clear result.",
    "suggestions": ["Add the situation.", "Quantify the result."],
    "improved_answer": "Rewrite.",
}


def test_valid_feedback():
    assert validate_feedback(GOOD) == []


def test_score_out_of_range():
    bad = {**GOOD, "scores": {**GOOD["scores"], "clarity": 7}}
    assert any("clarity" in e for e in validate_feedback(bad))


def test_wrong_suggestion_count():
    assert validate_feedback({**GOOD, "suggestions": ["only one"]})


def test_question_count():
    assert validate_questions({"questions": [{"question": "Q1"}]}, 3)


def test_answer_length_checks():
    assert check_answer("too short") is not None
    assert check_answer("word " * 100) is None
    assert check_posting("short") is not None


def test_parse_json_strips_fences():
    assert parse_json('```json\n{"a": 1}\n```') == {"a": 1}
