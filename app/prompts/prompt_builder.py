"""Builds prompts for each rewrite mode."""
from __future__ import annotations

from app.models.enums import PromptMode

_SHARED_GUARDRAILS = (
    "Return only the resulting text. "
    "Do not add explanations, labels, or commentary. "
    "Do not wrap the answer in quotation marks. "
    "Do not use bullet points unless the original text already used them. "
    "Preserve the original language of the text."
)

_MODE_INSTRUCTIONS = {
    PromptMode.CORRECT_GRAMMAR: (
        "Correct the grammar, spelling, and obvious sentence-structure issues only. "
        "Keep the original meaning and tone unchanged."
    ),
    PromptMode.MAKE_IT_BETTER: (
        "Improve this text for clarity, fluency, and professionalism "
        "while keeping the original meaning. Make it sound natural."
    ),
    PromptMode.SUPER: (
        "Rewrite this text to be polished, professional, clear, and impactful "
        "while preserving the original intent."
    ),
}


def build_system_prompt(mode: PromptMode) -> str:
    return f"{_MODE_INSTRUCTIONS[mode]} {_SHARED_GUARDRAILS}"


def build_user_prompt(text: str) -> str:
    return text
