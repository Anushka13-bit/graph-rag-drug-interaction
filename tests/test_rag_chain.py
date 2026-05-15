"""Tests for RAG answer validation."""

from __future__ import annotations

from reasoning.answer_validator import validate_answer


def test_validate_answer_extracts_fields() -> None:
    text = (
        "Interaction Summary: example\n"
        "Interaction Type: mechanism\n"
        "Confidence Level: Medium\n"
    )
    v = validate_answer(text, "omeprazole warfarin evidence")
    assert v.interaction_type == "mechanism"
    assert v.confidence == "Medium"
