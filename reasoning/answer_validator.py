"""Post-process LLM answers for structure and conservative grounding."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class ValidatedAnswer:
    text: str
    confidence: str
    interaction_type: Optional[str]


def _parse_interaction_type(text: str) -> Optional[str]:
    m = re.search(
        r"Interaction Type\s*[:\-]\s*(effect|mechanism|advise|pharmacokinetic|unknown)",
        text,
        re.IGNORECASE,
    )
    return m.group(1).lower() if m else None


def _parse_confidence(text: str) -> str:
    m = re.search(r"Confidence Level\s*[:\-]\s*(High|Medium|Low)", text, re.IGNORECASE)
    if m:
        return m.group(1).capitalize()
    return "Low"


def _strip_ungrounded(text: str, context: str) -> str:
    """Remove sentences that reference drugs not present in context (heuristic)."""
    ctx_lower = context.lower()
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    kept: list[str] = []
    for s in sentences:
        words = re.findall(r"\b[A-Z][a-z]+\b", s)
        if not words:
            kept.append(s)
            continue
        if any(w.lower() in ctx_lower for w in words):
            kept.append(s)
        elif "insufficient evidence" in s.lower():
            kept.append(s)
    return " ".join(kept) if kept else text


def validate_answer(answer: str, context: str) -> ValidatedAnswer:
    """Extract confidence/type and apply light grounding checks."""
    itype = _parse_interaction_type(answer)
    conf = _parse_confidence(answer)
    if not context.strip() or "none)" in context.lower():
        conf = "Low"
    text = _strip_ungrounded(answer, context)
    if "insufficient evidence" in answer.lower():
        conf = "Low"
    return ValidatedAnswer(text=text, confidence=conf, interaction_type=itype)
